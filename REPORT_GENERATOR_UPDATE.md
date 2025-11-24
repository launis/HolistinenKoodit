# Report Generator Update Summary

## Changes Made

Updated `report_generator.py` to support the new **TuomioJaPisteet** interface structure while maintaining backward compatibility with the old format.

## New JSON Structure Support

The report generator now correctly handles the new interface:

```typescript
interface TuomioJaPisteet extends BaseJSON {
  pisteet: {
    analyysi_ja_prosessi: {
      arvosana: 1 | 2 | 3 | 4;
      perustelu: string;
    };
    arviointi_ja_argumentaatio: {
      arvosana: 1 | 2 | 3 | 4;
      perustelu: string;
    };
    synteesi_ja_luovuus: {
      arvosana: 1 | 2 | 3 | 4;
      perustelu: string;
    };
  };
}
```

## Key Updates

### 1. Score Field Priority
The `get_criteria_data()` function now checks for fields in this order:
- `arvosana` (new format)
- `pisteet` (alternative)
- `taso` (old format)

### 2. Updated Search Keys
Each criterion now searches for the new key names first:

**Kriteeri 1: Analyysi ja Prosessin Tehokkuus**
- Primary: `analyysi_ja_prosessi`
- Fallback: `kriteeri_1_analyysi`, `analyysi`

**Kriteeri 2: Arviointi ja Argumentaatio**
- Primary: `arviointi_ja_argumentaatio`
- Fallback: `kriteeri_2_reflektio`, `kriteeri_2_prosessi_ohjaus`, `kriteeri_2_vuorovaikutus`, `vuorovaikutus`

**Kriteeri 3: Synteesi ja Luovuus**
- Primary: `synteesi_ja_luovuus`
- Fallback: `kriteeri_3_synteesi`, `synteesi`

### 3. Improved Case-Insensitive Matching
Fixed the `_find_value()` function to properly convert search keys to lowercase for consistent matching.

## Backward Compatibility

The system maintains full backward compatibility with:
- Old `pisteytys` structure
- `taso` field instead of `arvosana`
- `kuvaus` field instead of `perustelu`

## Testing

Created comprehensive tests in `test_both_formats.py` that verify:
- ✅ New format with `pisteet.analyysi_ja_prosessi` + `arvosana`
- ✅ Old format with `pisteytys.kriteeri_1_analyysi` + `taso`

## Result

**OSA 2: ANALYYTTINEN ARVIOINTI** now correctly displays:
- **Pistemäärä**: Shows actual scores (e.g., "4/4") instead of "N/A/4"
- **Perustelu**: Shows the full description from the JSON file

Both new and old JSON formats are fully supported.
