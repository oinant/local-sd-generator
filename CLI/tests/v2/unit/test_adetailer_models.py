"""
Unit tests for ADetailer data models
"""

import pytest
from templating.models.adetailer import ADetailerDetector, ADetailerConfig


class TestADetailerDetector:
    """Test ADetailerDetector data model"""

    def test_minimal_detector(self):
        """Test detector with minimal config"""
        detector = ADetailerDetector(ad_model="face_yolov9c.pt")

        assert detector.ad_model == "face_yolov9c.pt"
        assert detector.ad_prompt == ""
        assert detector.ad_negative_prompt == ""
        assert detector.ad_confidence == 0.3
        assert detector.ad_mask_k_largest == 1
        assert detector.ad_denoising_strength == 0.4

    def test_full_detector_config(self):
        """Test detector with full custom config"""
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
            ad_steps=50,
            ad_use_cfg_scale=True,
            ad_cfg_scale=8.5
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
        assert detector.ad_use_cfg_scale is True
        assert detector.ad_cfg_scale == 8.5

    def test_detector_defaults(self):
        """Test detector default values match SD WebUI defaults"""
        detector = ADetailerDetector(ad_model="test.pt")

        # Check critical defaults
        assert detector.ad_confidence == 0.3
        assert detector.ad_mask_k_largest == 1
        assert detector.ad_mask_blur == 4
        assert detector.ad_dilate_erode == 4
        assert detector.ad_denoising_strength == 0.4
        assert detector.ad_inpaint_only_masked is True
        assert detector.ad_inpaint_only_masked_padding == 32
        assert detector.ad_use_steps is False
        assert detector.ad_steps == 28
        assert detector.ad_use_cfg_scale is False


class TestADetailerConfig:
    """Test ADetailerConfig container"""

    def test_single_detector(self):
        """Test config with single detector"""
        detector = ADetailerDetector(ad_model="face_yolov9c.pt")
        config = ADetailerConfig(detectors=[detector])

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
        config = ADetailerConfig(detectors=[face_detector, hand_detector])

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
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()

        assert 'ADetailer' in api_dict
        adetailer_payload = api_dict['ADetailer']
        assert 'args' in adetailer_payload

        args = adetailer_payload['args']
        assert args[0] is True  # ad_enable
        assert args[1] is False  # skip_img2img
        assert args[2] == "face_yolov9c.pt"  # ad_model (1st detector)
        assert args[7] == 0.5  # ad_denoising_strength (1st detector)

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
        config = ADetailerConfig(detectors=[face_detector, hand_detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        # First detector config (indices 2-73)
        assert args[2] == "face_yolov9c.pt"  # 1st ad_model

        # Second detector config (indices 74-145)
        assert args[74] == "hand_yolov8n.pt"  # 2nd ad_model

    def test_to_api_dict_empty_detectors(self):
        """Test conversion with no detectors returns None"""
        config = ADetailerConfig(detectors=[])

        api_dict = config.to_api_dict()

        assert api_dict is None

    def test_api_dict_has_correct_structure(self):
        """Test that API dict follows SD WebUI structure"""
        detector = ADetailerDetector(ad_model="test.pt")
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()

        # Should have top-level ADetailer key with args array
        assert isinstance(api_dict, dict)
        assert 'ADetailer' in api_dict
        assert 'args' in api_dict['ADetailer']
        assert isinstance(api_dict['ADetailer']['args'], list)

        # Args should have 146 elements (2 + 72*2 for 2 detectors)
        args = api_dict['ADetailer']['args']
        assert len(args) == 146

    def test_api_dict_prompts_merged(self):
        """Test that ad_prompt and ad_negative_prompt are correctly placed"""
        detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_prompt="beautiful eyes, detailed face",
            ad_negative_prompt="blurry, distorted"
        )
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        assert args[3] == "beautiful eyes, detailed face"  # ad_prompt
        assert args[4] == "blurry, distorted"  # ad_negative_prompt

    def test_api_dict_boolean_flags(self):
        """Test boolean flags are correctly set"""
        detector = ADetailerDetector(
            ad_model="test.pt",
            ad_use_steps=True,
            ad_use_cfg_scale=True,
            ad_use_checkpoint=False,
            ad_restore_face=True
        )
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        assert args[20] is True   # ad_use_steps
        assert args[22] is True   # ad_use_cfg_scale
        assert args[24] is False  # ad_use_checkpoint
        assert args[35] is True   # ad_restore_face

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
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        assert args[2] == "face_yolov9c.pt"
        assert args[5] == 0.3   # confidence
        assert args[6] == 1     # mask_k_largest
        assert args[7] == 0.5   # denoising
        assert args[8] == 4     # mask_blur
        assert args[9] == 4     # dilate_erode
        assert args[13] == 32   # padding
        assert args[20] is True # use_steps
        assert args[21] == 40   # steps

    def test_hand_fix_preset(self):
        """Test hand fix preset (2 hands)"""
        detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_mask_k_largest=2,
            ad_denoising_strength=0.4,
            ad_use_steps=True,
            ad_steps=40
        )
        config = ADetailerConfig(detectors=[detector])

        api_dict = config.to_api_dict()
        args = api_dict['ADetailer']['args']

        assert args[2] == "hand_yolov8n.pt"
        assert args[6] == 2     # mask_k_largest (2 hands)
        assert args[7] == 0.4   # denoising
        assert args[21] == 40   # steps
