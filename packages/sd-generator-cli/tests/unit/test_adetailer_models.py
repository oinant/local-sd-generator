"""
Unit tests for ADetailer data models
"""

import pytest
from sd_generator_cli.templating.models.config_models import ADetailerDetector, ADetailerConfig


class TestADetailerDetector:
    """Test ADetailerDetector data model"""

    def test_minimal_detector(self):
        """Test detector with default values"""
        detector = ADetailerDetector(ad_model="face_yolov9c.pt")

        assert detector.ad_model == "face_yolov9c.pt"
        assert detector.ad_prompt == ""
        assert detector.ad_negative_prompt == ""
        assert detector.ad_confidence == 0.3
        assert detector.ad_mask_k_largest == 0
        assert detector.ad_denoising_strength == 0.4

    def test_full_detector_config(self):
        """Test detector with custom config"""
        detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_prompt="perfect hands",
            ad_negative_prompt="distorted",
            ad_confidence=0.5,
            ad_mask_k_largest=2,
            ad_mask_blur=8,
            ad_dilate_erode=6,
            ad_denoising_strength=0.6,
            ad_inpaint_only_masked_padding=64,
            ad_use_steps=True,
            ad_steps=50
        )

        assert detector.ad_model == "hand_yolov8n.pt"
        assert detector.ad_prompt == "perfect hands"
        assert detector.ad_negative_prompt == "distorted"
        assert detector.ad_confidence == 0.5
        assert detector.ad_mask_k_largest == 2
        assert detector.ad_mask_blur == 8
        assert detector.ad_dilate_erode == 6
        assert detector.ad_denoising_strength == 0.6
        assert detector.ad_inpaint_only_masked_padding == 64
        assert detector.ad_use_steps is True
        assert detector.ad_steps == 50

    def test_detector_to_api_dict(self):
        """Test conversion to API dict format"""
        detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_denoising_strength=0.5,
            ad_steps=40,
            ad_use_steps=True
        )

        api_dict = detector.to_api_dict()

        assert api_dict['ad_model'] == "face_yolov9c.pt"
        assert api_dict['ad_denoising_strength'] == 0.5
        assert api_dict['ad_steps'] == 40
        assert api_dict['ad_use_steps'] is True
        assert 'ad_confidence' in api_dict
        assert 'ad_mask_k' in api_dict  # API uses ad_mask_k, not ad_mask_k_largest
        assert 'ad_mask_filter_method' in api_dict  # New required field


class TestADetailerConfig:
    """Test ADetailerConfig container"""

    def test_single_detector(self):
        """Test config with single detector"""
        detector = ADetailerDetector(ad_model="face_yolov9c.pt")
        config = ADetailerConfig(enabled=True, detectors=[detector])

        assert config.enabled is True
        assert len(config.detectors) == 1
        assert config.detectors[0].ad_model == "face_yolov9c.pt"

    def test_multiple_detectors(self):
        """Test config with multiple detectors (face + hand)"""
        face_detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_denoising_strength=0.5
        )
        hand_detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_mask_k_largest=2,
            ad_denoising_strength=0.4
        )
        config = ADetailerConfig(enabled=True, detectors=[face_detector, hand_detector])

        assert len(config.detectors) == 2
        assert config.detectors[0].ad_model == "face_yolov9c.pt"
        assert config.detectors[1].ad_model == "hand_yolov8n.pt"
        assert config.detectors[1].ad_mask_k_largest == 2

    def test_to_api_dict_single_detector(self):
        """Test conversion to SD WebUI API format (single detector)"""
        detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_denoising_strength=0.5,
            ad_steps=40,
            ad_use_steps=True,
            ad_mask_k_largest=1
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        api_dict = config.to_api_dict()

        assert 'ADetailer' in api_dict
        adetailer_payload = api_dict['ADetailer']
        assert 'args' in adetailer_payload
        # Format: [enable, skip_img2img, detector1_dict]
        assert len(adetailer_payload['args']) == 3
        assert adetailer_payload['args'][0] is True  # Enable ADetailer
        assert adetailer_payload['args'][1] is False  # Skip img2img

        detector_dict = adetailer_payload['args'][2]  # First detector is at index 2
        assert detector_dict['ad_model'] == "face_yolov9c.pt"
        assert detector_dict['ad_denoising_strength'] == 0.5

    def test_to_api_dict_multiple_detectors(self):
        """Test conversion with multiple detectors"""
        face_detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_denoising_strength=0.5
        )
        hand_detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_denoising_strength=0.4
        )
        config = ADetailerConfig(enabled=True, detectors=[face_detector, hand_detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        # Format: [enable, skip_img2img, detector1_dict, detector2_dict]
        assert len(args) == 4
        assert args[0] is True  # Enable ADetailer
        assert args[1] is False  # Skip img2img
        assert args[2]['ad_model'] == "face_yolov9c.pt"
        assert args[3]['ad_model'] == "hand_yolov8n.pt"

    def test_to_api_dict_empty_detectors(self):
        """Test conversion with no detectors returns None"""
        config = ADetailerConfig(enabled=True, detectors=[])

        api_dict = config.to_api_dict()

        assert api_dict is None

    def test_to_api_dict_disabled(self):
        """Test conversion with enabled=False returns None"""
        detector = ADetailerDetector(ad_model="test.pt")
        config = ADetailerConfig(enabled=False, detectors=[detector])

        api_dict = config.to_api_dict()

        assert api_dict is None

    def test_high_quality_face_preset(self):
        """Test realistic high-quality face preset"""
        detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_confidence=0.3,
            ad_mask_k_largest=1,
            ad_mask_blur=4,
            ad_dilate_erode=4,
            ad_denoising_strength=0.5,
            ad_inpaint_only_masked_padding=32,
            ad_use_steps=True,
            ad_steps=40
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        api_dict = config.to_api_dict()
        detector_dict = api_dict['ADetailer']['args'][2]  # First detector is at index 2

        assert detector_dict['ad_model'] == "face_yolov9c.pt"
        assert detector_dict['ad_confidence'] == 0.3
        assert detector_dict['ad_mask_k'] == 1  # API uses ad_mask_k
        assert detector_dict['ad_denoising_strength'] == 0.5
        assert detector_dict['ad_mask_blur'] == 4
        assert detector_dict['ad_dilate_erode'] == 4
        assert detector_dict['ad_inpaint_only_masked_padding'] == 32
        assert detector_dict['ad_use_steps'] is True
        assert detector_dict['ad_steps'] == 40

    def test_hand_fix_preset(self):
        """Test hand fix preset (2 hands)"""
        detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_mask_k_largest=2,
            ad_denoising_strength=0.4,
            ad_use_steps=True,
            ad_steps=40
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        api_dict = config.to_api_dict()
        detector_dict = api_dict['ADetailer']['args'][2]  # First detector is at index 2

        assert detector_dict['ad_model'] == "hand_yolov8n.pt"
        assert detector_dict['ad_mask_k'] == 2  # API uses ad_mask_k
        assert detector_dict['ad_denoising_strength'] == 0.4
        assert detector_dict['ad_steps'] == 40
