# https://www.webpages.uidaho.edu/vakanski/Multispectral_Images_Dataset.html

import csv
import glob
import os
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from urllib.parse import unquote, urlparse

import numpy as np
import supervisely as sly
from dataset_tools.convert import unpack_if_archive
from dotenv import load_dotenv
from supervisely.io.fs import (
    dir_exists,
    file_exists,
    get_file_ext,
    get_file_name,
    get_file_name_with_ext,
    get_file_size,
)
from tqdm import tqdm

import src.settings as s


def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path


def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count


def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    # project_name = "Potato Plants Images"
    dataset_path = "/mnt/d/datasetninja-raw/multispectral-potato-plants-images"
    batch_size = 30
    imgs_ext = ".png"
    anns_ext = ".xml"
    group_tag_name = "im_id"

    def create_ann(image_path):
        labels = []
        tags = []

        id_data = get_file_name(image_path)
        group_id = sly.Tag(tag_id, value=id_data)
        tags.append(group_id)

        image_np = sly.imaging.image.read(image_path)[:, :, 0]
        img_height = image_np.shape[0]
        img_wight = image_np.shape[1]

        ann_data = im_name_to_anns[get_file_name_with_ext(image_path)]
        for curr_ann_data in ann_data:
            class_name = curr_ann_data[4]
            if class_name == "st":
                class_name = "stressed"
            obj_class = meta.get_obj_class(class_name)
            top = int(curr_ann_data[1])
            left = int(curr_ann_data[0])
            bottom = int(curr_ann_data[3])
            right = int(curr_ann_data[2])

            rect = sly.Rectangle(left=left, top=top, right=right, bottom=bottom)
            label = sly.Label(rect, obj_class)
            labels.append(label)

        return sly.Annotation(img_size=(img_height, img_wight), labels=labels, img_tags=tags)

    obj_class_healthy = sly.ObjClass("healthy", sly.Rectangle)
    obj_class_stressed = sly.ObjClass("stressed", sly.Rectangle)
    tag_id = sly.TagMeta("im_id", sly.TagValueType.ANY_STRING)

    group_tag_meta = sly.TagMeta(group_tag_name, sly.TagValueType.ANY_STRING)

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(obj_classes=[obj_class_healthy, obj_class_stressed])
    meta = meta.add_tag_meta(group_tag_meta)
    api.project.update_meta(project.id, meta.to_json())
    api.project.images_grouping(id=project.id, enable=True, tag_name=group_tag_name)

    ds_to_data = {
        "train": ("/RGB_Images/Train_Images", "/Spectral_Images/*/Train_Images"),
        "test": ("/RGB_Images/Test_Images", "/Spectral_Images/*/Test_Images"),
    }

    ds_to_labels_rgb = {"train": "Train_Labels_CSV.csv", "test": "Test_Labels_CSV.csv"}
    ds_to_labels_spectral = {"train": "Train_Labels_CSV.csv", "test": "Test_labels_CSV.csv"}

    for ds_name, images_data in ds_to_data.items():
        dataset = api.dataset.create(project.id, ds_name, change_name_if_conflict=True)
        for index, images_folder in enumerate(images_data):
            ann_csv_path = os.path.join(dataset_path, "RGB_Images", ds_to_labels_rgb[ds_name])
            if index == 1:
                ann_csv_path = os.path.join(
                    dataset_path, "Spectral_Images/Labels", ds_to_labels_spectral[ds_name]
                )

            im_name_to_anns = defaultdict(list)
            with open(ann_csv_path, "r") as file:
                csvreader = csv.reader(file)
                for idx, row in enumerate(csvreader):
                    if idx == 0:
                        continue
                    im_name_to_anns[row[0].split("/")[1]].append(row[1:])
            images_pathes = glob.glob(dataset_path + images_folder + "/*.jpg")

            progress = sly.Progress("Create dataset {}".format(ds_name), len(images_pathes))

            for img_pathes_batch in sly.batched(images_pathes, batch_size=batch_size):
                img_names_batch = [get_file_name_with_ext(im_path) for im_path in img_pathes_batch]

                if index == 1:
                    img_names_batch = [
                        im_path.split("/")[-3] + "_" + get_file_name_with_ext(im_path)
                        for im_path in img_pathes_batch
                    ]

                img_infos = api.image.upload_paths(dataset.id, img_names_batch, img_pathes_batch)
                img_ids = [im_info.id for im_info in img_infos]

                anns = [create_ann(image_path) for image_path in img_pathes_batch]
                api.annotation.upload_anns(img_ids, anns)

                progress.iters_done_report(len(img_names_batch))
    return project
