import os
import pandas as pd
import pytest
from typing import List, Tuple

from src.bulk_changes.get_data import (
    read_imei_and_setting,
    read_imei_only,
    deduplicate_imeis,
)


def create_temp_csv(content: str, filename: str) -> None:
    """
    Helper function to create a temporary CSV file with the given content.

    Args:
        content (str): The content to write into the file.
        filename (str): The name of the file to create.
    """
    with open(filename, "w") as f:
        f.write(content)


@pytest.fixture(autouse=True)
def cleanup() -> None:
    """
    Fixture to clean up temporary files after each test.
    """
    yield
    for file in ["test_imei.csv", "test_imei_settings.csv"]:
        if os.path.exists(file):
            os.remove(file)


@pytest.mark.asyncio
async def test_read_imei_only_no_header() -> None:
    """
    Test reading IMEIs from a file without a header.
    """
    content = "123456789012345\n987654321098765\n123456789012345"
    create_temp_csv(content, "test_imei.csv")

    result: List[str] = await read_imei_only("test_imei.csv")
    assert len(result) == 2
    assert result == ["123456789012345", "987654321098765"]


@pytest.mark.asyncio
async def test_read_imei_only_with_header() -> None:
    """
    Test reading IMEIs from a file with a header.
    """
    content = "IMEI\n123456789012345\n987654321098765"
    create_temp_csv(content, "test_imei.csv")

    result: List[str] = await read_imei_only("test_imei.csv")
    assert len(result) == 2
    assert result == ["123456789012345", "987654321098765"]


@pytest.mark.asyncio
async def test_read_imei_and_setting_no_header() -> None:
    """
    Test reading IMEIs and settings from a file without a header.
    """
    content = "123456789012345,setting1\n987654321098765,setting2"
    create_temp_csv(content, "test_imei_settings.csv")

    imeis: List[str]
    settings: List[str]
    imeis, settings = await read_imei_and_setting("test_imei_settings.csv")
    assert len(imeis) == 2
    assert len(settings) == 2
    assert imeis == ["123456789012345", "987654321098765"]
    assert settings == ["setting1", "setting2"]


@pytest.mark.asyncio
async def test_read_imei_and_setting_with_header() -> None:
    """
    Test reading IMEIs and settings from a file with a header.
    """
    content = "IMEI,Setting\n123456789012345,setting1\n987654321098765,setting2"
    create_temp_csv(content, "test_imei_settings.csv")

    imeis: List[str]
    settings: List[str]
    imeis, settings = await read_imei_and_setting("test_imei_settings.csv")
    assert len(imeis) == 2
    assert len(settings) == 2
    assert imeis == ["123456789012345", "987654321098765"]
    assert settings == ["setting1", "setting2"]


@pytest.mark.asyncio
async def test_imei_in_second_column() -> None:
    """
    Test reading IMEIs from a file where IMEI is in the second column.
    """
    content = "ID,IMEI,Setting\n1,123456789012345,setting1\n2,987654321098765,setting2"
    create_temp_csv(content, "test_imei_settings.csv")

    imeis: List[str]
    settings: List[str]
    imeis, settings = await read_imei_and_setting("test_imei_settings.csv")
    assert len(imeis) == 2
    assert imeis == ["123456789012345", "987654321098765"]


@pytest.mark.asyncio
async def test_case_sensitive_headers() -> None:
    """
    Test that the function correctly handles different case variations of headers.
    """
    headers = ["IMEI", "Imei", "imei"]
    for header in headers:
        content = (
            f"{header},Setting\n123456789012345,setting1\n987654321098765,setting2"
        )
        create_temp_csv(content, "test_imei_settings.csv")

        imeis: List[str]
        settings: List[str]
        imeis, settings = await read_imei_and_setting("test_imei_settings.csv")
        assert len(imeis) == 2
        assert imeis == ["123456789012345", "987654321098765"]


@pytest.mark.asyncio
async def test_deduplicate_imeis() -> None:
    """
    Test deduplication of IMEIs with corresponding settings.
    """
    imeis = ["123456789012345", "987654321098765", "123456789012345"]
    settings = ["setting1", "setting2", "setting3"]

    unique_imeis: List[str]
    unique_settings: List[str]
    unique_imeis, unique_settings = await deduplicate_imeis(imeis, settings)
    assert len(unique_imeis) == 2
    assert unique_imeis == ["123456789012345", "987654321098765"]
    assert unique_settings == ["setting1", "setting2"]


@pytest.mark.asyncio
async def test_empty_file() -> None:
    """
    Test handling of an empty file.
    """
    create_temp_csv("", "test_imei.csv")

    with pytest.raises(pd.errors.EmptyDataError, match="No columns to parse from file"):
        await read_imei_only("test_imei.csv")


@pytest.mark.asyncio
async def test_file_with_only_invalid_imeis() -> None:
    """
    Test handling of a file with only invalid IMEIs.
    """
    content = "IMEI\n12345\n1234567890"
    create_temp_csv(content, "test_imei.csv")

    with pytest.raises(ValueError, match="No valid IMEI numbers found in the file."):
        await read_imei_only("test_imei.csv")


@pytest.mark.asyncio
async def test_file_with_invalid_and_valid_imeis() -> None:
    """
    Test handling of a file with both invalid and valid IMEIs.
    """
    content = "IMEI\n12345\n1234567890123456\n987654321098765"
    create_temp_csv(content, "test_imei.csv")

    result: List[str] = await read_imei_only("test_imei.csv")
    assert len(result) == 2
    assert set(result) == {"123456789012345", "987654321098765"}


@pytest.mark.asyncio
async def test_file_without_imei_column() -> None:
    """
    Test handling of a file without an IMEI column.
    """
    content = "ID,Name\n1,John\n2,Jane"
    create_temp_csv(content, "test_imei.csv")

    with pytest.raises(ValueError, match="No IMEI column found."):
        await read_imei_only("test_imei.csv")


@pytest.mark.asyncio
async def test_large_file() -> None:
    """
    Test handling of a large file with 100,000 IMEIs.
    """
    imeis = [f"{i:015d}" for i in range(100000)]
    content = "IMEI\n" + "\n".join(imeis)
    create_temp_csv(content, "test_imei.csv")

    result: List[str] = await read_imei_only("test_imei.csv")
    assert len(result) == 100000


@pytest.mark.asyncio
async def test_imei_and_setting_mapping() -> None:
    """
    Test correct mapping of IMEIs to settings.
    """
    content = """IMEI,Setting,ExtraColumn
123456789012345,SettingA,Extra1
987654321098765,SettingB,Extra2
567890123456789,SettingC,Extra3"""
    create_temp_csv(content, "test_imei_settings.csv")

    imeis: List[str]
    settings: List[str]
    imeis, settings = await read_imei_and_setting("test_imei_settings.csv")

    assert len(imeis) == 3
    assert len(settings) == 3

    expected_mapping = [
        ("123456789012345", "SettingA"),
        ("987654321098765", "SettingB"),
        ("567890123456789", "SettingC"),
    ]

    for (imei, setting), (expected_imei, expected_setting) in zip(
            zip(imeis, settings), expected_mapping
    ):
        assert imei == expected_imei, f"IMEI mismatch: {imei} != {expected_imei}"
        assert (
                setting == expected_setting
        ), f"Setting mismatch: {setting} != {expected_setting}"
