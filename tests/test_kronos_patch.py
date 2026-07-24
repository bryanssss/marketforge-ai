from __future__ import annotations

from scripts.patch_kronos_compat import patch_text


def test_patch_preserves_existing_amount_in_predict_and_batch() -> None:
    source = """        if self.vol_col not in df.columns:
            df[self.vol_col] = 0.0
        df[self.amt_vol] = 0.0  # Fill missing amount with zeros
        if self.amt_vol not in df.columns and self.vol_col in df.columns:
            df[self.amt_vol] = df[self.vol_col] * df[self.price_cols].mean(axis=1)
        df[self.amt_vol] = 0.0
        if self.amt_vol not in df.columns and self.vol_col in df.columns:
            df[self.amt_vol] = df[self.vol_col] * df[self.price_cols].mean(axis=1)
"""
    patched, count = patch_text(source)
    assert count == 2
    assert "df[self.amt_vol] = 0.0" not in patched
    assert patched.count("if self.amt_vol not in df.columns:") == 2
