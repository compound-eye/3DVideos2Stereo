#!/bin/bash

# make sure conda environment is correct
# make sure ffmpeg is installed
# make sure movies are named as listed in movie_names.txt
# movies located at /mnt/nas/vishrut/datasets/movies/

ce_home=$1
movies_dir=$2
movie_list_filename=$3
data_lists=$4

if [ -z "$movie_list_filename" ]
then
    movie_list_filename="movie_names.txt"
    data_lists=(lists/train.txt lists/validation.txt lists/test.txt)
fi

while IFS= read -r movie
do
    echo "converting $movie to sbs"
    ./convertToSbs.sh $movies_dir $movie
    echo "extracting frames for $movie"
    ./run_extractFrames.sh $movie
    num_chapters=`ls image_left/$movie | wc -l`
    for chapter in $(seq 1 $num_chapters)
    do
	echo "processing $movie chapter $chapter"
	# creating dir will also be done in the python script
	# but its easier to force proper permissions this way
	mkdir -p reconstructions/$movie/chapter$chapter/
	chmod -R g+w reconstructions/
	PYTHONPATH=$ce_home python3 reconstructionFlow.py --movie=$movie --chapter=$chapter --ce_repo=$ce_home
    done
done < $movie_list_filename

for data_list in $(data_lists)
do
    PYTHONPATH=$ce_home python3 get_disp_and_uncertainty.py $data_list
    PYTHONPATH=$ce_home python3 create_dataset_csv.py $data_list ${MY_FILE/txt/csv}
done
