import math
import re
import shutil

from pandas import read_excel
from matplotlib import pyplot
from PIL import Image


def draw_graph(url, distance_to_references_list):
    file = read_excel(url)

    first_type = [[], []]
    second_type = [[], []]
    third_type = [[], []]
    unknown_type = [[], []]

    classes = list(file["class"])
    nodes = list(file["node"])
    ends = list(file["end"])
    references_x = list(file["centre(x)"])
    references_y = list(file["centre(y)"])

    iterator = 0
    for class_type in classes:
        if class_type == "first":
            first_type[0].append(nodes[iterator])
            first_type[1].append(ends[iterator])
        elif class_type == "second":
            second_type[0].append(nodes[iterator])
            second_type[1].append(ends[iterator])
        elif class_type == "third":
            third_type[0].append(nodes[iterator])
            third_type[1].append(ends[iterator])
        else:
            unknown_type[0].append(nodes[iterator])
            unknown_type[1].append(ends[iterator])
        iterator += 1
    print("first class:\n")
    print(first_type[0])
    print(first_type[1])
    print("\nsecond class:\n")
    print(second_type[0])
    print(second_type[1])
    print("\nthird class:\n")
    print(third_type[0])
    print(third_type[1])
    print("\nunknown class:\n")
    print(unknown_type[0])
    print(unknown_type[1])

    pyplot.plot(first_type[1], first_type[0], "ro")
    pyplot.plot(second_type[1], second_type[0], "bo")
    pyplot.plot(third_type[1], third_type[0], "go")
    pyplot.plot(unknown_type[1][0], unknown_type[0][0], "yo")

    for reference_x, reference_y in zip(references_x, references_y):
        pyplot.plot(reference_x, reference_y, "co")
        pyplot.plot(reference_x, reference_y, "co")
        pyplot.plot(reference_x, reference_y, "co")
        pyplot.plot((unknown_type[1][0], reference_x), (unknown_type[0][0], reference_y), linestyle="-",
                    color="black")
        pyplot.plot((unknown_type[1][0], reference_x), (unknown_type[0][0], reference_y), linestyle="-", color="black")
        pyplot.plot((unknown_type[1][0], reference_x), (unknown_type[0][0], reference_y), linestyle="-", color="black")

    pyplot.xlabel("Ne")
    pyplot.ylabel("Nnd")
    pyplot.show()


def read_image(image_path):
    pixel_rgb_values_list = []
    with open(image_path, "rb") as unknown_image:
        pixel_data = Image.open(unknown_image).getdata()
        for pixel in pixel_data:
            pixel_rgb_values_list.append(pixel)

    return pixel_rgb_values_list


def read_all_recognized_images(path_to_excel):
    file = read_excel(path_to_excel)
    list_of_paths = list(file["path"])
    counter_first, counter_second, counter_third = 0, 0, 0
    pixel_rgb_values_per_class = []
    for path in list_of_paths:
        if str(path).find("first") != -1:
            counter_first += 1
            pixel_rgb_values_per_class.append(read_image(path))
        elif str(path).find("second") != -1:
            counter_second += 1
            pixel_rgb_values_per_class.append(read_image(path))
        elif str(path).find("third") != -1:
            counter_third += 1
            pixel_rgb_values_per_class.append(read_image(path))

    return pixel_rgb_values_per_class


def get_reference_avg_brightness_per_class(pixel_rgb_values_per_class):
    average_brightness_per_class = [[], [], []]
    average_brightness_per_class[0] = [0] * 900
    average_brightness_per_class[1] = [0] * 900
    average_brightness_per_class[2] = [0] * 900
    counter = 0
    for image_rgb_values in pixel_rgb_values_per_class:
        rgb_value_counter = 0
        for rgb_value in image_rgb_values:
            r, g, b, a = rgb_value
            if counter < 5:
                average_brightness_per_class[0][rgb_value_counter] += b
            elif 4 < counter < 10:
                average_brightness_per_class[1][rgb_value_counter] += b
            elif 10 <= counter < 15:
                average_brightness_per_class[2][rgb_value_counter] += b
            rgb_value_counter += 1
        counter += 1

    first_class_avg_values = [value // 5 for value in average_brightness_per_class[0]]
    second_class_avg_values = [value // 5 for value in average_brightness_per_class[1]]
    third_class_avg_values = [value // 5 for value in average_brightness_per_class[2]]

    average_brightness_per_class[0] = first_class_avg_values
    average_brightness_per_class[1] = second_class_avg_values
    average_brightness_per_class[2] = third_class_avg_values

    return average_brightness_per_class


def get_distance_list_to_each_reference(average_brightness_per_class, pixel_rgb_values_list):
    distance_to_references_list = []
    for reference_avg_values_list in average_brightness_per_class:
        intermediate_results = []
        counter = 0
        for reference_value in reference_avg_values_list:
            intermediate_results.append((pixel_rgb_values_list[counter][2] - reference_value) ** 2)
            counter += 1
        distance_to_references_list.append(math.sqrt(sum(intermediate_results)))
    print(distance_to_references_list)
    return distance_to_references_list


def get_class_type(distance_to_references_list):
    if distance_to_references_list.index(min(distance_to_references_list)) == 0:
        return "first"
    elif distance_to_references_list.index(min(distance_to_references_list)) == 1:
        return "second"
    elif distance_to_references_list.index(min(distance_to_references_list)) == 2:
        return "third"


def recognize_in_excel(path_to_excel, class_type, distances_to_references):
    file = read_excel(path_to_excel)
    file.at[file.index[-1], "class"] = class_type
    for i in range(0, len(distances_to_references)):
        file.at[file.index[i], "distance"] = distances_to_references[i]
    if path_to_excel == "data_images.xlsx":
        copy_file_to_recognized(
            file.at[file.index[-1], "path"], "images/recognized/" + class_type + str(len(list(file["path"]))) + ".png"
        )
        file.at[file.index[-1], "path"] = "images/recognized/" + class_type + str(len(list(file["path"]))) + ".png"
    file.to_excel(path_to_excel, index=False)


def recognize_from_data_excel():
    file = read_excel("data.xlsx")
    list_of_centres_x = list(file["centre(x)"])
    list_of_centres_y = list(file["centre(y)"])
    unknown_x = file.at[file.index[-1], "end"]
    unknown_y = file.at[file.index[-1], "node"]
    list_of_centres_x = list_of_centres_x[0:3]
    list_of_centres_y = list_of_centres_y[0:3]

    distance_to_references_list = []
    for i in range(0, len(list_of_centres_x)):
        distance_to_references_list.append(
            math.sqrt(((list_of_centres_x[i] - unknown_x) ** 2 + (list_of_centres_y[i] - unknown_y) ** 2))
        )
    recognize_in_excel("data.xlsx", get_class_type(distance_to_references_list), distance_to_references_list)


def fill_excel_number_and_class_columns(excel_path):
    file = read_excel(excel_path)
    list_of_paths = list(file["path"])
    list_of_search_results = []
    numbers_for_n_col = []
    types_for_class_col = []
    for path in list_of_paths:
        list_of_search_results.append(re.search("/([fFsStTUu])(.+\\d+)", path).group())
    print(list_of_search_results)
    for search_result in list_of_search_results:
        types_for_class_col.append(re.search("[a-zA-Z]+", search_result)[0])
        numbers_for_n_col.append(re.search("[0-9]+", search_result)[0])
    for i in range(0, len(numbers_for_n_col)):
        file.at[i, "n"] = numbers_for_n_col[i]
        file.at[i, "class"] = types_for_class_col[i]
    file.to_excel(excel_path, index=False)


def copy_file_to_recognized(path_to_file, path_to_move):
    shutil.move(path_to_file, path_to_move)


if __name__ == '__main__':
    excel_file = read_excel("data_images.xlsx")
    paths_list = list(excel_file["path"])
    # draw_graph("data.xlsx")

    fill_excel_number_and_class_columns("data_images.xlsx")

    distances_to_references_list = get_distance_list_to_each_reference(
        get_reference_avg_brightness_per_class(read_all_recognized_images("data_images.xlsx")),
        read_image(paths_list[-1])
    )
    draw_graph("data.xlsx", distances_to_references_list)
    recognize_in_excel(
        "data_images.xlsx",
        get_class_type(distances_to_references_list),
        distances_to_references_list
    )
    # recognize_from_data_excel()
