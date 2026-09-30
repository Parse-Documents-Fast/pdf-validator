from dev.core.checksum import calculate_checksum


def test_checksum_determinism():
    content = b"hello world"
    checksum1 = calculate_checksum(content)
    checksum2 = calculate_checksum(content)
    assert checksum1 == checksum2
    assert checksum1 == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

def test_checksum_empty():
    content = b""
    checksum = calculate_checksum(content)
    assert checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
