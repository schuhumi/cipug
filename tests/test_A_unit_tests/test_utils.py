from cipug.utils import clean_image_hash


def test_clean_image_hash():
    # Test cases: (input, expected_output)
    test_cases = [
        ("sha256:1234567890abcdef1234567890abcdef", "1234567890abcdef1234567890abcdef"),
        ("docker.io/library/alpine@sha256:1234567890abcdef1234567890abcdef", "1234567890abcdef1234567890abcdef"),
        ("alpine:latest", "latest"),
        ("my-image:tag-with-dashes", "tagwithdashes"),
        ("my-image:tag.with.dots", "tagwithdots"),
        ("justhash", "justhash"),
        ("", ""),
        (None, None),
    ]

    for input_hash, expected in test_cases:
        assert clean_image_hash(input_hash) == expected
