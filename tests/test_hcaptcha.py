from bot.hcaptcha import (
    crop_box_for_frame,
    frame_index,
    is_valid_jpeg,
    parse_image_url,
    parse_sprite_frame,
)


def test_parse_image_url_extracts_url():
    style = 'background: url("https://imgs.hcaptcha.com/abc123") 50% 50% / 36px 36px no-repeat;'
    assert parse_image_url(style) == "https://imgs.hcaptcha.com/abc123"


def test_parse_image_url_returns_none_when_missing():
    assert parse_image_url("width: 120px;") is None


def test_is_valid_jpeg_accepts_jpeg_magic_bytes():
    assert is_valid_jpeg(b"\xff\xd8\xff\xe0rest of jpeg data")


def test_is_valid_jpeg_rejects_html_error_page():
    assert not is_valid_jpeg(b"<!doctype html><html>...")


REFERENCE_STYLE = (
    "position: absolute; top: 50%; left: 50%; z-index: 5; width: 90px; height: 360px; "
    'margin-left: -45px; margin-top: -135px; background: url("https://x") '
    "50% 50% / 90px 360px no-repeat;"
)


def test_parse_sprite_frame_extracts_fields():
    sprite = parse_sprite_frame(REFERENCE_STYLE, frame_height=90)
    assert sprite is not None
    assert sprite.url == "https://x"
    assert sprite.sprite_width == 90.0
    assert sprite.sprite_height == 360.0
    assert sprite.margin_top == -135.0


def test_frame_index_matches_visible_frame():
    sprite = parse_sprite_frame(REFERENCE_STYLE, frame_height=90)
    assert frame_index(sprite) == 1


def test_crop_box_for_frame_scales_to_raw_image_size():
    sprite = parse_sprite_frame(REFERENCE_STYLE, frame_height=90)
    assert crop_box_for_frame(sprite, 110, 440) == (0, 110, 110, 220)
