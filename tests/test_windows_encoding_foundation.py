"""Tests for cross-platform encoding issues (e.g., Windows cp1252)."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from amplifier_foundation.bundle import Bundle, PreparedBundle


class TestWindowsEncoding:
    """Tests for Windows encoding compatibility."""

    def test_bundle_can_read_utf8_context_file(self) -> None:
        """Ensures Bundle.prepare() can read context files with UTF-8 chars."""
        # This is a non-cp1252 character that would fail on Windows default encoding
        content = "Test with non-cp1252 char: ‘…“”’"

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            context_file = tmp_path / "context.md"
            context_file.write_text(content, encoding="utf-8")

            bundle = Bundle(
                name="encoding-test",
                base_path=tmp_path,
                context={"utf8_file": context_file},
                instruction="Instruction with @utf8_file",
            )

            # The factory re-reads the file, which is where the error would occur
            # The async part is not strictly necessary for this test but aligns with the
            # real implementation which is async.
            async def run_test():
                # We don't need a full session, just the PreparedBundle to get the factory
                # Mock a resolver to avoid needing a full prepare() call
                class MockResolver:
                    pass
                prepared = PreparedBundle(mount_plan={}, resolver=MockResolver(), bundle=bundle)
                factory = prepared._create_system_prompt_factory(bundle, session=None)
                system_prompt = await factory()

                # Assert that the content was read correctly and is in the prompt
                assert content in system_prompt
                assert "‘…“”’" in system_prompt

            # Run the async test function
            asyncio.run(run_test())
