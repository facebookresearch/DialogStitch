# Download CLEVR images.
# pip install gdown
# wget https://dl.fbaipublicfiles.com/clevr/CLEVR_v1.0.zip data/
# Download CLEVR-Dialog dataset.
# gdown https://drive.google.com/uc?id=1u6YABdNSfBrnV7CXVp5cfOSstGK0gyaE
# gdown https://drive.google.com/uc?id=1efCk917eT_vgDO__OS6cKZkC8stT5OL7

# python visualize_dialogs.py \
#     --input_json_path="data/deep_clevr_dialog_train.json"


python merge_dialogs.py \
    --clevr_train_json="data/clevr_train_raw_70k.json" \
    --clevr_val_json="data/clevr_val_raw_70k.json" \
    --save_root="data/" --num_workers=8

# Compute dependencies.
# python evaluate_dependence.py \
#     --input_clevr_path="data/clevr_train_raw_70k.json" \
#     --input_deep_clevr_path="data/deep_clevr_dialog_train.json"
