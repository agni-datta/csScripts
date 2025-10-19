#!/usr/bin/env python3
"""
Image to Nord Palette Converter Service.

This module provides comprehensive functionality for converting images to the Nord color
palette using various processing modes and algorithms. It implements service-oriented
architecture with clear separation of concerns for color math, palette operations,
pixel mapping, and orchestration.

The converter supports multiple processing modes:
- Exact mode: LAB nearest-color mapping with memory-aware tiling
- Quantize mode: Pillow quantization with optional Floyd-Steinberg dithering
- Auto mode: Automatically selects the best processing mode

Features:
- High-quality color space conversions (sRGB, XYZ, LAB)
- Memory-efficient tiling for large images
- Alpha channel preservation
- EXIF orientation correction
- Configurable blend strength for softening effects
- Support for multiple output formats (PNG, JPEG, WebP)

Dependencies:
    - numpy: For vectorized color space calculations
    - pillow: For image I/O and processing operations

Example:
    >>> from image_to_nord_converter import ImageToNordConversionService
    >>> converter = ImageToNordConversionService()
    >>> result_image = converter.convert_image_to_nord_palette(input_image)
    >>> converter.save_converted_image(result_image, "output.png")
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import List, Tuple

from PIL import Image, ImageOps

import numpy as np


@dataclass(frozen=True)
class CommandLineArguments:
    """
    Immutable data structure containing parsed command-line arguments.

    This class encapsulates all the configuration parameters needed for the
    image conversion process, ensuring type safety and immutability.

    Attributes:
        input_file_path: Path to the input image file.
        output_file_path: Path where the converted image will be saved.
        dithering_strategy: Dithering algorithm to use ("none" or "fs").
        processing_mode: Conversion mode ("auto", "exact", or "quantize").
        blend_strength: Intensity of the conversion effect (0.0 to 1.0).
        maximum_tile_pixel_count: Maximum pixels per processing tile for exact mode.
    """

    input_file_path: str
    output_file_path: str
    dithering_strategy: str
    processing_mode: str
    blend_strength: float
    maximum_tile_pixel_count: int


class ColorSpaceConversionService:
    """
    Service for performing color space conversions between sRGB, XYZ, and LAB.

    This service provides static methods for converting between different color
    spaces using industry-standard transformations. All methods work with NumPy
    arrays and are optimized for vectorized operations.

    The service uses D65 white point and standard sRGB primaries for all
    conversions, ensuring consistent and accurate color reproduction.
    """

    # Constants for sRGB to linear RGB conversion
    _SRGB_ALPHA: float = 0.055
    _SRGB_DELTA: float = 6.0 / 29.0

    # D65 white point coordinates for XYZ color space
    _D65_WHITE_POINT_X: float = 0.95047
    _D65_WHITE_POINT_Y: float = 1.00000
    _D65_WHITE_POINT_Z: float = 1.08883

    # Transformation matrices for RGB <-> XYZ conversion
    _RGB_TO_XYZ_MATRIX: np.ndarray = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    )

    _XYZ_TO_RGB_MATRIX: np.ndarray = np.array(
        [
            [3.2404542, -1.5371385, -0.4985314],
            [-0.9692660, 1.8760108, 0.0415560],
            [0.0556434, -0.2040259, 1.0572252],
        ],
        dtype=np.float64,
    )

    @staticmethod
    def convert_srgb_to_linear_rgb(srgb_values: np.ndarray) -> np.ndarray:
        """
        Convert sRGB values to linear RGB values.

        This method implements the standard sRGB to linear RGB conversion
        using the gamma correction formula specified in the sRGB standard.

        Args:
            srgb_values: Array containing sRGB values. Can be uint8 or float.
                        Expected shape: (..., 3).

        Returns:
            Array containing linear RGB values in range [0, 1].
            Shape: (..., 3), dtype: float32.
        """
        normalized_values = srgb_values.astype(np.float32) / 255.0
        alpha = ColorSpaceConversionService._SRGB_ALPHA
        return np.where(
            normalized_values <= 0.04045,
            normalized_values / 12.92,
            ((normalized_values + alpha) / (1 + alpha)) ** 2.4,
        )

    @staticmethod
    def convert_linear_rgb_to_srgb(linear_rgb_values: np.ndarray) -> np.ndarray:
        """
        Convert linear RGB values to sRGB values.

        This method implements the inverse sRGB conversion using the
        standard gamma correction formula.

        Args:
            linear_rgb_values: Array containing linear RGB values in range [0, 1].
                              Expected shape: (..., 3).

        Returns:
            Array containing sRGB values in range [0, 1].
            Shape: (..., 3), dtype: float.
        """
        alpha = ColorSpaceConversionService._SRGB_ALPHA
        return np.where(
            linear_rgb_values <= 0.0031308,
            12.92 * linear_rgb_values,
            (1 + alpha) * (linear_rgb_values ** (1 / 2.4)) - alpha,
        )

    @staticmethod
    def convert_rgb_to_xyz(linear_rgb_values: np.ndarray) -> np.ndarray:
        """
        Convert linear RGB values to XYZ color space using D65 white point.

        Args:
            linear_rgb_values: Array containing linear RGB values in range [0, 1].
                              Expected shape: (..., 3).

        Returns:
            Array containing XYZ values.
            Shape: (..., 3), dtype: float.
        """
        return linear_rgb_values @ ColorSpaceConversionService._RGB_TO_XYZ_MATRIX.T

    @staticmethod
    def convert_xyz_to_rgb(xyz_values: np.ndarray) -> np.ndarray:
        """
        Convert XYZ color space values to linear RGB using D65 white point.

        Args:
            xyz_values: Array containing XYZ values.
                        Expected shape: (..., 3).

        Returns:
            Array containing linear RGB values.
            Shape: (..., 3), dtype: float.
        """
        return xyz_values @ ColorSpaceConversionService._XYZ_TO_RGB_MATRIX.T

    @staticmethod
    def _apply_xyz_to_lab_transformation(xyz_channel_values: np.ndarray) -> np.ndarray:
        """
        Apply the standard transformation function for XYZ to LAB conversion.

        This helper function implements the piecewise function used in the
        CIE LAB color space conversion standard.

        Args:
            xyz_channel_values: Array of normalized XYZ channel values.

        Returns:
            Array of transformed channel values according to CIE standard.
        """
        delta = ColorSpaceConversionService._SRGB_DELTA
        return np.where(
            xyz_channel_values > delta**3,
            np.cbrt(xyz_channel_values),
            (xyz_channel_values / (3 * delta**2)) + (4 / 29),
        )

    @staticmethod
    def _apply_lab_to_xyz_transformation(
        transformed_channel_values: np.ndarray,
    ) -> np.ndarray:
        """
        Apply the inverse transformation function for LAB to XYZ conversion.

        This helper function implements the inverse of the piecewise function
        used in the CIE LAB color space conversion standard.

        Args:
            transformed_channel_values: Array of transformed channel values.

        Returns:
            Array of recovered normalized XYZ channel values.
        """
        delta = ColorSpaceConversionService._SRGB_DELTA
        return np.where(
            transformed_channel_values > delta,
            transformed_channel_values**3,
            3 * delta**2 * (transformed_channel_values - 4 / 29),
        )

    @staticmethod
    def convert_xyz_to_lab(xyz_values: np.ndarray) -> np.ndarray:
        """
        Convert XYZ color space values to CIELAB using D65 white point.

        Args:
            xyz_values: Array containing XYZ values.
                        Expected shape: (..., 3).

        Returns:
            Array containing LAB values [L, a, b].
            Shape: (..., 3), dtype: float.
        """
        white_point_x = ColorSpaceConversionService._D65_WHITE_POINT_X
        white_point_y = ColorSpaceConversionService._D65_WHITE_POINT_Y
        white_point_z = ColorSpaceConversionService._D65_WHITE_POINT_Z

        normalized_x = xyz_values[..., 0] / white_point_x
        normalized_y = xyz_values[..., 1] / white_point_y
        normalized_z = xyz_values[..., 2] / white_point_z

        transformed_x = ColorSpaceConversionService._apply_xyz_to_lab_transformation(
            normalized_x
        )
        transformed_y = ColorSpaceConversionService._apply_xyz_to_lab_transformation(
            normalized_y
        )
        transformed_z = ColorSpaceConversionService._apply_xyz_to_lab_transformation(
            normalized_z
        )

        lightness = 116 * transformed_y - 16
        a_channel = 500 * (transformed_x - transformed_y)
        b_channel = 200 * (transformed_y - transformed_z)

        return np.stack([lightness, a_channel, b_channel], axis=-1)

    @staticmethod
    def convert_lab_to_xyz(lab_values: np.ndarray) -> np.ndarray:
        """
        Convert CIELAB values to XYZ color space using D65 white point.

        Args:
            lab_values: Array containing LAB values [L, a, b].
                        Expected shape: (..., 3).

        Returns:
            Array containing XYZ values.
            Shape: (..., 3), dtype: float.
        """
        white_point_x = ColorSpaceConversionService._D65_WHITE_POINT_X
        white_point_y = ColorSpaceConversionService._D65_WHITE_POINT_Y
        white_point_z = ColorSpaceConversionService._D65_WHITE_POINT_Z

        lightness = lab_values[..., 0]
        a_channel = lab_values[..., 1]
        b_channel = lab_values[..., 2]

        transformed_y = (lightness + 16) / 116
        transformed_x = transformed_y + (a_channel / 500)
        transformed_z = transformed_y - (b_channel / 200)

        x_coordinate = (
            ColorSpaceConversionService._apply_lab_to_xyz_transformation(transformed_x)
            * white_point_x
        )
        y_coordinate = (
            ColorSpaceConversionService._apply_lab_to_xyz_transformation(transformed_y)
            * white_point_y
        )
        z_coordinate = (
            ColorSpaceConversionService._apply_lab_to_xyz_transformation(transformed_z)
            * white_point_z
        )

        return np.stack([x_coordinate, y_coordinate, z_coordinate], axis=-1)

    @staticmethod
    def convert_rgb_u8_to_lab(rgb_values: np.ndarray) -> np.ndarray:
        """
        Convert sRGB uint8 values to CIELAB float values.

        This is a convenience method that combines multiple conversion steps
        into a single operation for common use cases.

        Args:
            rgb_values: Array containing sRGB values as uint8.
                        Expected shape: (..., 3).

        Returns:
            Array containing LAB values [L, a, b].
            Shape: (..., 3), dtype: float.
        """
        linear_rgb = ColorSpaceConversionService.convert_srgb_to_linear_rgb(rgb_values)
        xyz_values = ColorSpaceConversionService.convert_rgb_to_xyz(linear_rgb)
        return ColorSpaceConversionService.convert_xyz_to_lab(xyz_values)

    @staticmethod
    def convert_lab_to_rgb_u8(lab_values: np.ndarray) -> np.ndarray:
        """
        Convert CIELAB float values to sRGB uint8 values.

        This is a convenience method that combines multiple conversion steps
        into a single operation for common use cases.

        Args:
            lab_values: Array containing LAB values [L, a, b].
                        Expected shape: (..., 3).

        Returns:
            Array containing sRGB values as uint8.
            Shape: (..., 3), dtype: uint8.
        """
        xyz_values = ColorSpaceConversionService.convert_lab_to_xyz(lab_values)
        linear_rgb = ColorSpaceConversionService.convert_xyz_to_rgb(xyz_values)
        srgb_values = np.clip(
            ColorSpaceConversionService.convert_linear_rgb_to_srgb(linear_rgb), 0, 1
        )
        return (srgb_values * 255.0 + 0.5).astype(np.uint8)


class NordColorPaletteService:
    """
    Service for managing the Nord color palette and performing nearest-neighbor queries.

    This service provides functionality to work with the Nord color palette,
    including color space conversions and nearest-neighbor color matching
    using LAB color space for perceptual accuracy.
    """

    # Nord color palette in hexadecimal format
    _NORD_HEX_COLORS: List[str] = [
        "#2E3440",  # Polar Night 0
        "#3B4252",  # Polar Night 1
        "#434C5E",  # Polar Night 2
        "#4C566A",  # Polar Night 3
        "#D8DEE9",  # Snow Storm 0
        "#E5E9F0",  # Snow Storm 1
        "#ECEFF4",  # Snow Storm 2
        "#8FBCBB",  # Frost 0
        "#88C0D0",  # Frost 1
        "#81A1C1",  # Frost 2
        "#5E81AC",  # Frost 3
        "#BF616A",  # Aurora Red
        "#D08770",  # Aurora Orange
        "#EBCB8B",  # Aurora Yellow
        "#A3BE8C",  # Aurora Green
        "#B48EAD",  # Aurora Purple
    ]

    def __init__(self) -> None:
        """
        Initialize the Nord color palette service.

        This constructor builds the RGB and LAB representations of the Nord
        palette for efficient color matching operations.
        """
        self.rgb_values: np.ndarray = self._build_rgb_array(self._NORD_HEX_COLORS)
        self.lab_values: np.ndarray = ColorSpaceConversionService.convert_rgb_u8_to_lab(
            self.rgb_values
        )

    @staticmethod
    def _convert_hex_string_to_rgb_tuple(hex_color_string: str) -> Tuple[int, int, int]:
        """
        Convert a hexadecimal color string to an RGB tuple.

        Args:
            hex_color_string: Hex color string in format "#RRGGBB" or "RRGGBB".

        Returns:
            Tuple containing RGB values in range [0, 255].
        """
        clean_hex_string = hex_color_string.strip().lstrip("#")
        rgb_values = tuple(int(clean_hex_string[i : i + 2], 16) for i in (0, 2, 4))
        return rgb_values[0], rgb_values[1], rgb_values[2]

    @classmethod
    def _build_rgb_array(cls, hex_color_list: List[str]) -> np.ndarray:
        """
        Build a NumPy array of RGB values from a list of hex color strings.

        Args:
            hex_color_list: List of hexadecimal color strings.

        Returns:
            NumPy array containing RGB values.
            Shape: (N, 3), dtype: uint8.
        """
        rgb_tuples = [
            cls._convert_hex_string_to_rgb_tuple(hex_color)
            for hex_color in hex_color_list
        ]
        return np.array(rgb_tuples, dtype=np.uint8)

    def find_nearest_color_indices_in_lab_space(
        self, rgb_color_block: np.ndarray
    ) -> np.ndarray:
        """
        Find the nearest Nord palette indices for a block of RGB colors using LAB space.

        This method performs nearest-neighbor color matching in the perceptually
        uniform LAB color space for accurate color reproduction.

        Args:
            rgb_color_block: Array containing RGB color values.
                            Expected shape: (N, 3), dtype: uint8.

        Returns:
            Array containing indices of nearest palette colors.
            Shape: (N,), dtype: int32.
        """
        lab_colors = ColorSpaceConversionService.convert_rgb_u8_to_lab(rgb_color_block)
        color_differences = lab_colors[:, None, :] - self.lab_values[None, :, :]
        squared_distances = np.sum(color_differences * color_differences, axis=2)
        return np.argmin(squared_distances, axis=1).astype(np.int32)

    def create_pillow_palette_image(self) -> Image.Image:
        """
        Create a Pillow palette-mode image encoding the Nord color palette.

        Returns:
            Pillow image in 'P' mode with Nord palette colors set as palette entries.
        """
        palette_image = Image.new("P", (16, 16))
        palette_data = [0] * (256 * 3)

        for color_index, (red, green, blue) in enumerate(self.rgb_values.tolist()):
            palette_data[color_index * 3 + 0] = red
            palette_data[color_index * 3 + 1] = green
            palette_data[color_index * 3 + 2] = blue

        palette_image.putpalette(palette_data)
        return palette_image


class ExactLabProcessingService:
    """
    Service for exact nearest-color mapping in LAB color space with memory-aware tiling.

    This service provides high-quality color mapping by processing images in tiles
    to manage memory usage efficiently, especially for large images.
    """

    def __init__(
        self,
        color_palette_service: NordColorPaletteService,
        maximum_tile_pixel_count: int,
    ) -> None:
        """
        Initialize the exact LAB processing service.

        Args:
            color_palette_service: Service providing Nord color palette functionality.
            maximum_tile_pixel_count: Maximum number of pixels per processing tile.
                                     Must be greater than or equal to 1.
        """
        self._color_palette_service = color_palette_service
        self._maximum_tile_pixel_count = max(1, int(maximum_tile_pixel_count))

    def process_image_with_exact_lab_mapping(
        self, input_image: Image.Image
    ) -> Image.Image:
        """
        Map an image to the Nord palette using LAB nearest neighbor matching.

        This method processes the image in tiles to maintain steady memory usage
        while preserving alpha channels throughout the conversion process.

        Args:
            input_image: Input Pillow image in any supported mode.

        Returns:
            Mapped image in RGB or RGBA mode, preserving the original alpha channel.
        """
        has_alpha_channel = "A" in input_image.getbands()
        rgb_image = input_image.convert("RGB")
        alpha_channel = input_image.split()[-1] if has_alpha_channel else None

        image_width, image_height = rgb_image.size
        output_image = Image.new("RGB", (image_width, image_height))

        tile_height = max(
            1, min(image_height, self._maximum_tile_pixel_count // max(1, image_width))
        )
        current_y_position = 0

        while current_y_position < image_height:
            tile_height_adjusted = min(tile_height, image_height - current_y_position)
            image_tile = np.array(
                rgb_image.crop(
                    (
                        0,
                        current_y_position,
                        image_width,
                        current_y_position + tile_height_adjusted,
                    )
                ),
                dtype=np.uint8,
            )
            flattened_tile = image_tile.reshape(-1, 3)
            nearest_color_indices = (
                self._color_palette_service.find_nearest_color_indices_in_lab_space(
                    flattened_tile
                )
            )
            mapped_tile = (
                self._color_palette_service.rgb_values[nearest_color_indices]
                .reshape(image_tile.shape)
                .astype(np.uint8)
            )
            output_image.paste(
                Image.fromarray(mapped_tile, mode="RGB"), (0, current_y_position)
            )
            current_y_position += tile_height_adjusted

        if has_alpha_channel and alpha_channel is not None:
            output_image = output_image.convert("RGBA")
            output_image.putalpha(alpha_channel)

        return output_image


class QuantizationProcessingService:
    """
    Service for Pillow-based quantization to a fixed palette with optional dithering.

    This service provides fast color quantization using Pillow's built-in algorithms
    with support for Floyd-Steinberg dithering to reduce color banding artifacts.
    """

    def __init__(
        self, color_palette_service: NordColorPaletteService, dithering_strategy: str
    ) -> None:
        """
        Initialize the quantization processing service.

        Args:
            color_palette_service: Service providing Nord color palette functionality.
            dithering_strategy: Dithering algorithm to use ("none" or "fs" for Floyd-Steinberg).
        """
        self._color_palette_service = color_palette_service
        self._palette_image = color_palette_service.create_pillow_palette_image()
        self._dithering_flag = (
            Image.Dither.FLOYDSTEINBERG
            if dithering_strategy == "fs"
            else Image.Dither.NONE
        )

    def process_image_with_quantization(self, input_image: Image.Image) -> Image.Image:
        """
        Quantize an image to the Nord color palette using Pillow's quantization.

        Args:
            input_image: Input Pillow image in any supported mode.

        Returns:
            Quantized image in RGB or RGBA mode, preserving the original alpha channel.
        """
        has_alpha_channel = "A" in input_image.getbands()
        rgb_image = input_image.convert("RGB")
        alpha_channel = input_image.split()[-1] if has_alpha_channel else None

        quantized_image = rgb_image.quantize(
            palette=self._palette_image,
            dither=self._dithering_flag,
            method=Image.Quantize.FASTOCTREE,
        )
        output_image = quantized_image.convert("RGBA" if has_alpha_channel else "RGB")

        if has_alpha_channel and alpha_channel is not None:
            output_image.putalpha(alpha_channel)

        return output_image


class ImageToNordConversionService:
    """
    High-level service that orchestrates image conversion to the Nord color palette.

    This service provides a unified interface for converting images to the Nord
    palette, handling EXIF orientation, processing mode selection, and optional
    blending with the original image for softer visual effects.
    """

    def __init__(
        self,
        processing_mode: str = "auto",
        dithering_strategy: str = "none",
        blend_strength: float = 1.0,
        maximum_tile_pixel_count: int = 20_000_000,
    ) -> None:
        """
        Initialize the image to Nord conversion service.

        Args:
            processing_mode: Processing mode ("auto", "exact", or "quantize").
            dithering_strategy: Dithering strategy ("none" or "fs").
            blend_strength: Blend weight toward the converted result (0.0 to 1.0).
            maximum_tile_pixel_count: Maximum pixels per tile for exact mode processing.

        Raises:
            ValueError: If any argument is outside its allowed range or set.
        """
        if processing_mode not in {"auto", "exact", "quantize"}:
            raise ValueError(
                "processing_mode must be one of {'auto', 'exact', 'quantize'}"
            )
        if dithering_strategy not in {"none", "fs"}:
            raise ValueError("dithering_strategy must be one of {'none', 'fs'}")
        if not (0.0 <= float(blend_strength) <= 1.0):
            raise ValueError("blend_strength must be in range [0, 1]")

        self._color_palette_service = NordColorPaletteService()
        self._processing_mode = processing_mode
        self._dithering_strategy = dithering_strategy
        self._blend_strength = float(blend_strength)
        self._maximum_tile_pixel_count = int(maximum_tile_pixel_count)

    @staticmethod
    def _blend_images_with_alpha_preservation(
        original_image: Image.Image, converted_image: Image.Image, blend_strength: float
    ) -> Image.Image:
        """
        Blend two images while preserving alpha channel information.

        Args:
            original_image: Original image for blending.
            converted_image: Converted image for blending.
            blend_strength: Blend factor toward converted image (0.0 to 1.0).

        Returns:
            Blended Pillow image with preserved alpha channel.
        """
        if blend_strength >= 1.0:
            return converted_image
        if blend_strength <= 0.0:
            return original_image

        has_alpha_channel = "A" in converted_image.getbands()
        if has_alpha_channel:
            original_rgb = original_image.convert("RGB")
            converted_rgb = converted_image.convert("RGB")
            alpha_channel = converted_image.split()[-1]
            blended_rgb = Image.blend(
                original_rgb, converted_rgb, blend_strength
            ).convert("RGBA")
            blended_rgb.putalpha(alpha_channel)
            return blended_rgb

        return Image.blend(
            original_image.convert("RGB"),
            converted_image.convert("RGB"),
            blend_strength,
        )

    def convert_image_to_nord_palette(self, input_image: Image.Image) -> Image.Image:
        """
        Convert an image to the Nord color palette using the configured processing mode.

        This method applies EXIF orientation correction, selects the appropriate
        processing mode, and optionally blends the result with the original image.

        Args:
            input_image: Input Pillow image to convert.

        Returns:
            Converted Pillow image using the Nord color palette.
        """
        corrected_image = ImageOps.exif_transpose(input_image)
        selected_mode = (
            self._processing_mode
            if self._processing_mode != "auto"
            else ("quantize" if self._dithering_strategy != "none" else "exact")
        )

        if selected_mode == "quantize":
            processing_service = QuantizationProcessingService(
                self._color_palette_service, dithering_strategy=self._dithering_strategy
            )
            converted_image = processing_service.process_image_with_quantization(
                corrected_image
            )
        elif selected_mode == "exact":
            processing_service = ExactLabProcessingService(
                self._color_palette_service,
                maximum_tile_pixel_count=self._maximum_tile_pixel_count,
            )
            converted_image = processing_service.process_image_with_exact_lab_mapping(
                corrected_image
            )
        else:
            # This path should be unreachable due to validation in __init__
            raise ValueError(
                "processing_mode must be one of {'auto', 'exact', 'quantize'}"
            )

        if 0.0 <= self._blend_strength < 1.0:
            converted_image = self._blend_images_with_alpha_preservation(
                corrected_image.convert(converted_image.mode),
                converted_image,
                self._blend_strength,
            )

        return converted_image

    @staticmethod
    def save_converted_image(image: Image.Image, output_path: str) -> None:
        """
        Save an image with optimized settings for common output formats.

        This method applies format-specific optimizations including PNG compression,
        JPEG quality settings, and WebP quality settings while handling alpha
        channel constraints for JPEG format.

        Args:
            image: Pillow image to save.
            output_path: Destination file path for the saved image.
        """
        output_file_path = Path(output_path)
        file_extension = output_file_path.suffix.lower()
        save_parameters = {}
        image_to_save = image

        if file_extension in (".jpg", ".jpeg"):
            save_parameters.update(dict(quality=95, subsampling=0, optimize=True))
            if image_to_save.mode == "RGBA":
                image_to_save = image_to_save.convert("RGB")
        elif file_extension == ".png":
            save_parameters.update(dict(optimize=True))
        elif file_extension in (".webp",):
            save_parameters.update(dict(quality=95, method=6))

        image_to_save.save(str(output_file_path), **save_parameters)


class ImageToNordCommandLineInterface:
    """
    Command-line interface for the Image to Nord conversion service.

    This class provides a comprehensive CLI for batch processing of images,
    including argument parsing, error handling, and user feedback.
    """

    @staticmethod
    def _generate_default_output_path(input_file_path: str) -> str:
        """
        Generate a default output filename by appending '_nord' before the file extension.

        Args:
            input_file_path: Path to the input image file.

        Returns:
            Suggested output file path with '_nord' suffix.
        """
        input_path = Path(input_file_path)
        output_stem = input_path.stem + "_nord"
        file_extension = input_path.suffix if input_path.suffix else ".png"
        return str(input_path.with_name(output_stem + file_extension))

    @staticmethod
    def parse_command_line_arguments(
        argument_vector: List[str],
    ) -> CommandLineArguments:
        """
        Parse command-line arguments from the provided argument vector.

        Args:
            argument_vector: List of command-line arguments excluding the program name.

        Returns:
            CommandLineArguments object with parsed and validated arguments.
        """
        argument_parser = argparse.ArgumentParser(
            description="Convert images to the Nord color palette."
        )
        argument_parser.add_argument("input", help="Path to the input image file")
        argument_parser.add_argument(
            "-o", "--output", help="Path to the output image file"
        )
        argument_parser.add_argument(
            "--dither",
            choices=["none", "fs"],
            default="none",
            help="Dithering algorithm for quantize mode",
        )
        argument_parser.add_argument(
            "--mode",
            choices=["auto", "exact", "quantize"],
            default="auto",
            help="Processing mode for color conversion",
        )
        argument_parser.add_argument(
            "--strength",
            type=float,
            default=1.0,
            help="Blend strength toward converted result [0.0..1.0]",
        )
        argument_parser.add_argument(
            "--max-tile-pixels",
            type=int,
            default=20_000_000,
            help="Maximum pixels per tile in exact mode",
        )

        parsed_namespace = argument_parser.parse_args(argument_vector)

        output_path = (
            parsed_namespace.output
            or ImageToNordCommandLineInterface._generate_default_output_path(
                parsed_namespace.input
            )
        )

        return CommandLineArguments(
            input_file_path=parsed_namespace.input,
            output_file_path=output_path,
            dithering_strategy=parsed_namespace.dither,
            processing_mode=parsed_namespace.mode,
            blend_strength=float(parsed_namespace.strength),
            maximum_tile_pixel_count=int(parsed_namespace.max_tile_pixels),
        )

    @staticmethod
    def execute_command_line_interface(argument_vector: List[str]) -> int:
        """
        Execute the command-line interface and return an appropriate exit code.

        Args:
            argument_vector: List of command-line arguments excluding the program name.

        Returns:
            Exit code: 0 for success, non-zero for various error conditions.
        """
        parsed_arguments = ImageToNordCommandLineInterface.parse_command_line_arguments(
            argument_vector
        )

        try:
            input_image = Image.open(parsed_arguments.input_file_path)
        except (IOError, OSError, ValueError) as exception:
            print(f"Failed to open input image: {exception}", file=sys.stderr)
            return 2

        try:
            conversion_service = ImageToNordConversionService(
                processing_mode=parsed_arguments.processing_mode,
                dithering_strategy=parsed_arguments.dithering_strategy,
                blend_strength=parsed_arguments.blend_strength,
                maximum_tile_pixel_count=parsed_arguments.maximum_tile_pixel_count,
            )
            converted_image = conversion_service.convert_image_to_nord_palette(
                input_image
            )
        except (ValueError, RuntimeError) as exception:
            print(f"Failed to convert image: {exception}", file=sys.stderr)
            return 3

        try:
            ImageToNordConversionService.save_converted_image(
                converted_image, parsed_arguments.output_file_path
            )
        except (IOError, OSError) as exception:
            print(f"Failed to save output image: {exception}", file=sys.stderr)
            return 4

        print(
            f"Successfully saved converted image: {parsed_arguments.output_file_path}"
        )
        return 0


def main() -> None:
    """
    Main entry point for module execution as a command-line script.

    This function serves as the primary entry point when the module is executed
    directly from the command line, handling argument parsing and execution flow.
    """
    sys.exit(
        ImageToNordCommandLineInterface.execute_command_line_interface(sys.argv[1:])
    )


if __name__ == "__main__":
    main()
