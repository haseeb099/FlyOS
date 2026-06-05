# Pretty Fly data for CashFly

CashFly loads CSVs from this folder by default (`DATA_DIR=../data` in `backend/.env`).

**Quick setup (no copy):** use the hackathon pack in place:

```text
DATA_DIR=../pretty_fly_data_pack/data
```

**Or** copy or junction the pack here:

```powershell
# Windows junction (one-time)
cmd /c mklink /J data ..\pretty_fly_data_pack\data
```

All 21 files are listed in `pretty_fly_data_pack/README.md`. Run reconciliation:

```bash
cd pretty_fly_data_pack
pip install -r requirements.txt
python validate.py data/
```
