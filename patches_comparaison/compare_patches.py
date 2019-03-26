from training_testing import create_test
import os
from scipy.spatial.distance import cdist, dice, cosine, euclidean, jaccard, braycurtis
from scipy.spatial import minkowski_distance
from unet3d.data import write_data_to_file, open_data_file
from unet3d.generator import  get_data_from_file, get_validation_split, create_patch_index_list, add_data
from unet3d.utils.patches import get_patch_from_3d_data
from unet3d.metrics import dice_coef_loss
import numpy as np
import pandas as pd
import random
import nibabel as nib
import itertools
import pickle

class Compare_patches:

    def __init__(self, conf):
        self.config = conf
        create = create_test.Test(self.config)
        self.fetch_testing_data_files = create.fetch_testing_data_files
        self.patch_shape = (16, 16, 16)


    def main(self, mode = "combination", overwrite_validation = True):

        combination_path = os.path.abspath("Data/generated_data/combination.pkl")

        results = np.empty((0, 4))
        index_list, validation_list, data_file = self.get_index_list()
        if overwrite_validation or not os.path.exists(combination_path):
            print("Creating new combination list")
            if mode == "one patch":
                combination_list = self.create_combination_one_patch(index_list, validation_list, data_file)
                x_a, y_a = get_data_from_file(data_file, combination_list[0][0], self.patch_shape)
            elif mode == "combination":
                combination_list = self.create_combination_list(index_list, validation_list)
            elif mode == "random":
                combination_list = self.create_combination_list_random(index_list, n_exp=50000)

            with open(combination_path, 'wb') as f:
                pickle.dump(combination_list, f)
        else:
            print("Loading found combination list")
            with open(combination_path, 'rb') as f:
                combination_list = pickle.load(f)


        for j, l in enumerate(combination_list):
            print(j/len(combination_list)*100, "%")
            if mode != "one patch":
                x_a, y_a = get_data_from_file(data_file, l[0], self.patch_shape)

            x_b, y_b = get_data_from_file(data_file, l[1], self.patch_shape)
            if np.mean(x_a) < -10 or np.mean(x_b) < -10:
                print("Mean is too low")
            else:
                c,d = self.compare_patches(x_a, y_a, x_b, y_b)
                results = np.vstack((results,np.asarray([float(c),float(d), l[0], l[1]])))

        results_df = pd.DataFrame(results, columns=["Patch Sim", "Truth Sim", "Patch A", "Patch B"])
        results_df["Patch Sim"] = pd.to_numeric(results_df["Patch Sim"])
        results_df["Truth Sim"] = pd.to_numeric(results_df["Truth Sim"])
        outputdir = os.path.abspath("results/sim_patches/results.csv")
        results_df.to_csv(outputdir)
        # self.select_patches(results_df, data_file)



    def get_index_list(self, overwrite_data=False, patch_overlap=0, patch_start_offset = None):
        '''
        Function to get the indexes of all the images and all the patches in the testing set.
        :param overwrite_data: If False it will read  previously written files
        :param patch_overlap:
        :param patch_start_offset:
        :return:
        '''
        self.config.validation_split = 0.0
        self.config.data_file = os.path.abspath("Data/generated_data/" + self.config.data_set + "_testing.h5")
        self.config.training_file = os.path.abspath(
            "Data/generated_data/" + self.config.data_set + "_testing.pkl")
        self.config.validation_file = os.path.abspath(
            "Data/generated_data/" + self.config.data_set + "_testing_validation_ids.pkl")
        # convert input images into an hdf5 file
        if overwrite_data or not os.path.exists(self.config.data_file):
            testing_files, subject_ids = self.fetch_testing_data_files(return_subject_ids=True)
            write_data_to_file(testing_files, self.config.data_file, image_shape=self.config.image_shape,
                               subject_ids=subject_ids)
        data_file_opened = open_data_file(self.config.data_file)

        training_list, validation_list = get_validation_split(data_file_opened,
                                                              data_split=0,
                                                              overwrite_data=overwrite_data,
                                                              training_file=self.config.training_file,
                                                              validation_file=self.config.validation_file)

        index_list = create_patch_index_list(validation_list, data_file_opened.root.data.shape[-3:], self.patch_shape,
                                             patch_overlap, patch_start_offset)

        return index_list, validation_list, data_file_opened

    def create_combination_one_patch(self, index_list, validation_list, data_file):
        '''
        We select one random patch to compare to all the other patches.
        The selected patch needs to have a GT and to have a mean above 0
        :param index_list: The index of all the patches
        :param validation_list: The index of all the validation images
        :return: A combination list between the selected patch and the others.
        '''
        combination_list = []
        subsample_val = random.sample(validation_list, k = 37)

        selected_patch = random.choice(validation_list)
        patch_A = random.choice([tup for tup in index_list if tup[0] == selected_patch])
        x_a, y_a = get_data_from_file(data_file, patch_A, self.patch_shape)
        print("Looking for a patch with mean above 0 and with a GT")
        while np.mean(x_a) < -1 or np.mean(y_a == 0):
            if np.mean(x_a) > -1 and np.mean(y_a) !=0:
                print("Found")
                print(np.mean(x_a) > 0, np.mean(y_a) !=0)
                break
            selected_patch = random.choice(validation_list)
            patch_A = random.choice([tup for tup in index_list if tup[0] == selected_patch])
            x_a, y_a = get_data_from_file(data_file, patch_A, self.patch_shape)
        for i in subsample_val:
            if selected_patch != i:
                list_b = [tup for tup in index_list if tup[0] == i]
                list_b = random.sample(list_b, k=32)
                for j in list_b:
                    combination_list.append((patch_A, j))
        return combination_list



    def create_combination_list(self, index_list, validation_list):

        combination_list = []
        subsample_val = random.choices(validation_list, k=37)
        for ind, i in enumerate(subsample_val):
            print("Creating combination list: ", ind/len(subsample_val)*100)
            list_a = [tup for tup in index_list if tup[0] == i]
            list_a = random.sample(list_a, k=30)
            for j in subsample_val:
                if i != j:
                    list_b = [tup for tup in index_list if tup[0] == j]
                    list_b = random.sample(list_b, k = 30)
                    for h in list_a:
                        for x in list_b:
                            combination_list.append((h, x))

            subsample_val.pop(0)
        return combination_list

    def create_combination_list_random(self, index_list, n_exp = 2000):
        combination_list = []
        while len(combination_list) < n_exp:
            a = random.choice(index_list)
            b = random.choice(index_list)
            if a[0] != b[0] and (a[1] != b[1]).all():
                combination_list.append((a,b))
        return combination_list


    def compare_patches(self, x_a, y_a, x_b, y_b):
        cov_x_a = np.cov(np.ravel(x_a))
        cov_x_b = np.cov(np.ravel(x_b))
        c = np.linalg.norm(cov_x_a-cov_x_b) #Frobenius norm

        cov_y_a = np.cov(np.ravel(y_a))
        cov_y_b = np.cov(np.ravel(y_b))
        d = np.linalg.norm(cov_y_a-cov_y_b)
        return c, d

    def select_patches(self, results_df, data_file):
        results_df = results_df.sort_values(by=["Patch Sim", "Truth Sim"])
        best = results_df.tail(10)
        print(results_df)
        print(results_df["Patch Sim"].corr(results_df["Truth Sim"]))
        for i in range(best.shape[0]):
            j = best.shape[0] - 1 - i
            index = best.iloc[j]["Patch A"][0]
            patch_position = best.iloc[j]["Patch A"][1]
            self.save_patch(index, patch_position, "A", data_file, i)

            index = best.iloc[j]["Patch B"][0]
            patch_position = best.iloc[j]["Patch B"][1]
            self.save_patch(index, patch_position, "B", data_file, i)

    def save_patch(self, index, patch_position, name, data_file, i):

        outputdir = os.path.abspath("results/sim_patches/"+str(i))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        data, truth = get_data_from_file(data_file, index, patch_shape=None)

        y = get_patch_from_3d_data(truth, self.patch_shape, patch_position)
        x = get_patch_from_3d_data(data, self.patch_shape, patch_position)
        x = np.reshape(x, (self.patch_shape))

        affine = data_file.root.affine[index]
        image = nib.Nifti1Image(x, affine)
        image.to_filename(os.path.join(outputdir, "patch_"+str(name)+"_" + str(i) + ".nii.gz"))
        image = nib.Nifti1Image(y, affine)
        image.to_filename(os.path.join(outputdir, "truth_"+str(name)+"_" + str(i) + ".nii.gz"))



