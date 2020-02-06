import logging
import warnings
warnings.filterwarnings('ignore')
import argparse

import flask
from flask import request, jsonify
from PIL import Image

import torch
from torchvision import transforms
from torchvision import datasets

from conf import settings
from utils import build_network

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.WARNING)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.CRITICAL)

logging.info('Start program')
handler = logging.FileHandler('infor.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

app = flask.Flask(__name__)
app.config["DEBUG"] = False

def predict_author_single_img(model, image_path):
    """
    
    """
    device = torch.device("cuda")
    image_transforms =  transforms.Compose([
                        transforms.Resize((112, 112)),
                        transforms.ToTensor(),
                        transforms.Normalize(settings.CIFAR100_TRAIN_MEAN, 
                                             settings.CIFAR100_TRAIN_STD)])

    img = Image.open(image_path)
    img_tensor = image_transforms(img)

    if torch.cuda.is_available():
        img_tensor = img_tensor.view(1, 3, 112, 112).cuda()
    else:
        img_tensor = img_tensor.view(1, 3, 112, 112)
    with torch.no_grad():
        model.eval()
        # model ouputs log probabilities
        out = model(img_tensor)  # <class 'torch.Tensor'>  torch.Size([1, 58])
        ps = torch.exp(out) #  <class 'torch.Tensor'> torch.Size([1, 58])
        topk, topclass = ps.topk(3, dim=1)
        
        sum_topk = int(topk.cpu().numpy()[0][0]) + int(topk.cpu().numpy()[0][1]) + int(topk.cpu().numpy()[0][2])
    return idx_to_class[topclass.cpu().numpy()[0][0]], (topk.cpu().numpy()[0][0])/sum_topk

@app.route('/sign_author_recognition', methods=["POST"])
def sign_recognition():
    global net
    global idx_to_class
    # example request: {"action":"recognition", "img_url":"D:/SealProjectOLD/Datasets/images/val/FukuohjiHorin/FukuohjiHorin_1_194-0486.jpg"}
    if request.method == "POST":
        if request.is_json:
            req = request.get_json()
            type_action = req["action"]
            img_url = req["img_url"]
            ####
            # add code to download image in here 
            ####
            img_path = img_url
            author, confidence = predict_author_single_img(net, img_path)
            print("author: ", author, " confidence: ", confidence)
        else:
            print("none json")
    
    result = {"author: ": author, " confidence: ": confidence}
    logging.info("author: " + author + " confidence: " +  confidence)
    return jsonify(result)

if __name__ == '__main__':
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    parser = argparse.ArgumentParser()
    parser.add_argument('-net', type=str, default= 'squeezenet', help='net type')
    parser.add_argument('-weights', type=str, default='./checkpoint/results/sign_squeezenet-280-regular.pth', help='the weights file path you want to test')
    parser.add_argument('-gpu', type=bool, default=True, help='use gpu or not')
    parser.add_argument('-w', type=int, default=4, help='number of workers for dataloader')
    parser.add_argument('-b', type=int, default=16, help='batch size for dataloader')
    parser.add_argument('-s', type=bool, default=True, help='whether shuffle the dataset')
    
    args_dict = vars(parser.parse_args())
    logger.info(args_dict)

    net_type = args_dict['net']
    use_gpu = args_dict['gpu']
    net = build_network(archi = net_type, use_gpu=use_gpu) 
    logger.info(net)

    net.load_state_dict(torch.load(args_dict['weights']), args_dict['gpu'])
    net.eval()

    example_image_dir = 'D:/SealProjectOLD/Datasets/images/val'
    dataset = datasets.ImageFolder(example_image_dir, transform= None)
    idx_to_class = {v: k for k, v in dataset.class_to_idx.items()}

    app.run()