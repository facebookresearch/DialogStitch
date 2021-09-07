## Stitching CLEVR-Dialog

This folder contains the code to stitch dialogs from a multimodal dialog, CLEVR-Dialog, using available metadata in order to obtain dialogs that are
deeper, have longer-term dependencies, and multiple contexts compared to
the source dataset.

### Setup
The code is based on Python 3.0+ and uses the following libraries (in addition to standard Python libraries):

```
pip install argparse
pip install tqdm
```

Download the original CLEVR-Dialog dataset from the [source][clevr_dialog_repo] and place the dataset files in `data/` of the `clevr_dialog/` folder.

Please see `run_me.sh` for example usage to obtain merged/stitched dialogs.

```
python merge_dialogs.py \
	--clevr_train_json="data/clevr_train_raw_70k.json" \
	--clevr_val_json="data/clevr_val_raw_70k.json" \
	--save_root="data/" \
	--num_workers=8
```

The dataset used for experiments in the paper can be obtained from `data/`.
The structure of the JSON data files is as follows:

```
{
	'image_filename': [<image filenames for stitched dialogs>],
	'image_index': [<image index for stitched dialogs>]
	'split': [<CLEVR-Dialog splits for stitched dialogs>],
	'dialog_index': [<Index from CLEVR-Dialog for stitched dialogs>],
	'data': [
		<caption>
		{
			'context_index': <Index from stitched dialogs>
			'caption': <str>,
		},
			...
	
		<question-answer pair>
		{
			'context_index': <Index from stitched dialogs>,
			'question': <str>,
			'answer': <str>,
		}
			...
	]
}
```

[clevr_dialog_repo]:https://github.com/satwikkottur/clevr-dialog