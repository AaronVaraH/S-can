# Air-Gapped Offline Operation & Maintenance Guide

## 1. Principles of Offline Edge Operation
The Edge Can-Inspector is architected to operate **independently of internet access or cloud connectivity**.
- **Inference**: Executes locally on the Raspberry Pi CPU / Hailo AI HAT+.
- **Data Persistence**: Records are stored in an embedded SQLite database (`data/inspection.db`).
- **Defect Standards & RAG Assistant**: Document indices are stored in local JSON/BM25 structures (`data/rag_index.json`), providing immediate technical retrieval without cloud LLMs.
- **Fail-Safe Operation**: If external network links drop, inspection, logging, and solenoid rejection continue with zero interruption.

---

## 2. Air-Gapped Model Updates via USB Drive

When deploying new model weights to a secure, isolated factory network:

### Step 1: Package Artifacts on Development Computer
On your GPU development station, export the model and manifest:
```bash
python scripts/export_model.py --output-dir staging_v2
```
Copy `staging_v2/can_detector.onnx` and `staging_v2/manifest.json` onto an encrypted USB drive.

### Step 2: Transfer to Raspberry Pi
Insert the USB drive into the Raspberry Pi:
```bash
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/can_detector.onnx /tmp/
cp /mnt/usb/manifest.json /tmp/
sudo umount /mnt/usb
```

### Step 3: Verified Atomic Deployment
Run the automated deployment script on the Pi:
```bash
python scripts/deploy_model.py --model /tmp/can_detector.onnx --manifest /tmp/manifest.json
```
The script will:
1. Verify SHA-256 integrity against the manifest.
2. Execute a test inference on the Pi ARM CPU to ensure operator compatibility.
3. Automatically archive the previously running model version.
4. Atomically swap the active production model.

---

## 3. Safe Rollback in Offline Environments
If the new model causes unexpected line behavior or false rejects:
```bash
python scripts/rollback_model.py
```
The system will instantly restore the previous verified model and manifest from `models/archive/` and update the registry without requiring internet or manual file renaming.

---

## 4. Updating Local Technical Documentation (RAG)
To add new factory SOPs, seamer calibration procedures, or customer defect criteria:
1. Drop the markdown file into `edge_inspector/rag/documents/` (e.g. `customer_x_spec.md`).
2. Rebuild the index:
```bash
python -c "from edge_inspector.rag import LocalDocumentIndexer; LocalDocumentIndexer().build_index()"
```
3. Operators can immediately query the updated knowledge base via the `/rag/query` REST API or local interface.
