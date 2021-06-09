#!/bin/bash

ce_home=$1
PYTHON="PYTHONPATH=$ce_home python3"

while IFS= read -r movie
do
    ./run_extractFrames.sh $movie
    num_chapters=`ls image_left/$movie | wc -l`
    for chapter in $(seq 1 $num_chapters)
    do
	echo "processing $movie chapter $chapter"
	$PYTHON reconstructionFlow.py --movie=$movie --chapter=$chapter --ce_repo=$ce_home
    done
done < "movie_names.txt"

$PYTHON get_disp_and_uncertainty.py lists/train.txt
$PYTHON get_disp_and_uncertainty.py lists/validation.txt
$PYTHON get_disp_and_uncertainty.py lists/test.txt

$PYTHON create_dataset_csv.py lists/train.txt
$PYTHON create_dataset_csv.py lists/validation.txt
$PYTHON create_dataset_csv.py lists/test.txt

# $PYTHON get_disp_and_uncertainty.py lists/debug.txt
# $PYTHON create_dataset_csv.py lists/debug.txt lists/debug.csv
