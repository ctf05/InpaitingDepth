import os
import shutil
from src import common_ui, core
import makeReels as r
from multiprocessing import Pool

input_folder = r'C:\Users\chris\IdeaProjects\Instagram Image\pics'
output_subfolder = "Videos"
numberOfConcurrent = 1

def remove_directory(directory_path):
    try:
        shutil.rmtree(directory_path)
        print(f"Directory '{directory_path}' has been removed successfully!")
    except Exception as e:
        print(f"Error removing directory '{directory_path}': {e}")


def start(concurrent):
    directories = os.listdir(input_folder)
    for i, subdir in enumerate(directories):

        if i % numberOfConcurrent != concurrent:
            continue

        if "Tall" not in subdir:
            continue

        subdir_path = os.path.join(input_folder, subdir)

        # Create the "TextPics" folder if it doesn't exist
        videos_path = os.path.join(subdir_path, output_subfolder)

        if not os.path.exists(videos_path):
            os.makedirs(videos_path)
        elif os.path.exists(os.path.join(subdir_path, "final_video.mp4")):
            continue

        if not os.path.exists(os.path.join(subdir_path, "10.png")):
            print(f"No 10.png found in {subdir_path}.")
            remove_directory(subdir_path)
            continue

        # Read texts from the 'texts.txt' file in the current directory
        texts_file_path = os.path.join(subdir_path, "captions.txt")
        if not os.path.exists(texts_file_path):
            print(f"No captions.txt found in {subdir_path}.")
            continue

        with open(texts_file_path, 'r') as file:
            texts = [line.strip() for line in file.readlines()]
            if (len(texts) != 10):
                print(f"Wrong number of texts in {subdir_path}.")
                continue
            for i in range(len(texts)):
                if texts[i][-1] == ",":
                    texts[i] = texts[i][:-1]
        print(f'concurrent: {concurrent} in f{subdir}')



        fps = 24

        totalWords = 0
        for text in texts:
            totalWords += len(text.split())
        averageWords = totalWords / len(texts)
        frames = round(((averageWords / 1.68) - 2) * fps)
        if frames / fps > 9:
            frames = 9 * fps
        print(frames / fps)

        #In the future, implement per text / video frame count instead of them all being averaged

        generate = True
        if (os.path.exists(os.path.join(videos_path, "10.mp4"))):
            generate = False
        if generate:
            #Delete all files in the 'out' folder
            for file in os.listdir(f'out{concurrent}'):
                file_path = os.path.join(f'out{concurrent}', file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)

            inputs = {
                'boost': True,
                'clipdepth': False,
                'clipdepth_far': 0,
                'clipdepth_mode': 'Range',
                'clipdepth_near': 1,
                'compute_device': 'GPU',
                'custom_depthmap': False,
                'custom_depthmap_img': None,
                'depthmap_batch_input_dir': f'{subdir_path}',
                'depthmap_batch_output_dir': f'out{concurrent}',
                'depthmap_batch_reuse': True,
                'depthmap_input_image': None,
                'depthmap_mode': '2',
                'depthmap_vm_compress_bitrate': 15000,
                'depthmap_vm_compress_checkbox': False,
                'depthmap_vm_custom': None,
                'depthmap_vm_custom_checkbox': False,
                'depthmap_vm_input': None,
                'depthmap_vm_smoothening_mode': 'experimental',
                'do_output_depth': True,
                'gen_inpainted_mesh': True,
                'gen_inpainted_mesh_demos': False,
                'gen_normalmap': False,
                'gen_rembg': False,
                'gen_simple_mesh': False,
                'gen_stereo': False,
                'image_batch': None,
                'model_type': 0,
                'net_height': 448,
                'net_size_match': False,
                'net_width': 448,
                'normalmap_invert': False,
                'normalmap_post_blur': False,
                'normalmap_post_blur_kernel': 3,
                'normalmap_pre_blur': False,
                'normalmap_pre_blur_kernel': 3,
                'normalmap_sobel': True,
                'normalmap_sobel_kernel': 3,
                'output_depth_combine': False,
                'output_depth_combine_axis': 'Horizontal',
                'output_depth_invert': False,
                'pre_depth_background_removal': False,
                'rembg_model': 'u2net',
                'save_background_removal_masks': False,
                'save_outputs': False,
                'simple_mesh_occlude': True,
                'simple_mesh_spherical': False,
                'stereo_balance': 0,
                'stereo_divergence': 2.5,
                'stereo_fill_algo': 'polylines_sharp',
                'stereo_modes': ['left-right', 'red-cyan-anaglyph'],
                'stereo_offset_exponent': 2,
                'stereo_separation': 0
            }


            #encoded_dict = {str(key): str(value) for key, value in inputs.items()}


            common_ui.run_generate_myself(inputs)

            #delete all files in the 'outputs' folder
            for file in os.listdir('outputs'):
                file_path = os.path.join('outputs', file)
                try:
                    if os.path.isfile(file_path) and f'_{concurrent}' in file:
                        os.unlink(file_path)
                except Exception as e:
                    print(e)


            traj = 1
            shift = "0.0,0.01,-0.13"
            vid_border = "0.09,0.06,0.12,0.06"
            dolly = True
            vid_format = "mp4"
            vid_ssaa = 3

            for i, file in enumerate(os.listdir(f'out{concurrent}')):
                path = os.path.join(f'out{concurrent}', file)
                core.run_makevideo(path, frames, fps, traj, shift, vid_border, dolly, vid_format, vid_ssaa, f'{concurrent}')

            for fileTwo in enumerate(os.listdir('outputs')):
                for i in range(1,11):
                    if f'{i}-' in fileTwo and f'_{concurrent}' in fileTwo:
                        os.rename(os.path.join('outputs', fileTwo), os.path.join('outputs', f'{i}.mp4'))
                        break


            for file in os.listdir('outputs'):
                if f"_{concurrent}" in file:
                    shutil.move(os.path.join("outputs", file), videos_path)

        video_paths = [os.path.join(videos_path, f'{i}.mp4') for i in range(1, 11)]
        print(video_paths)

        lengthPerVideo = frames / fps

        r.makeReel(subdir_path, video_paths, texts, True, lengthPerVideo)


def start_process(concurrent):
    print(f'Starting process {concurrent}')
    start(concurrent)

if __name__ == '__main__':
    # Setup a pool of processes and start them
    with Pool(numberOfConcurrent) as pool:
        pool.map(start_process, range(numberOfConcurrent))