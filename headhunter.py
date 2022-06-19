#!/usr/bin/python3
import boto3
import argparse
import os
import colorama
from termcolor import colored
from pathlib import Path
from rekognition_objects import RekognitionFace
from PIL import Image
import io

global intFileIndex
intFileIndex = 0
global dirFoundImages
dirFoundImages = './Found_Images'
accepted_extensions = ["jpg", "png", "jpeg"]
imageCompareDir = os.path.join(os.getcwd(), 'Images')
global intSuccessMatches
intSuccessMatches = 0
global bFindPerson
bFindPerson = False
colorama.init()
client=boto3.client('rekognition')
maxFaces=3

parser = argparse.ArgumentParser(description='Find face matches from one image or collection.')
parser.add_argument('target_resource', type=str,
                    help='path of the person image or collection name you want found')
parser.add_argument('-st', '--similarity-threshold', dest='similarity_threshold', type=int,
                    default=70, help='Minimum threshold allowed for face matches. Default is 70.')
parser.add_argument('-c', '--compare-directory', dest='compare_directory', type=str, default=None,
                    help='Is there another folder you would like to get comparision images from? Default is Current_Directory/Images/')
parser.add_argument('-o', '--output-file', dest='output_file_name', type=str, default='success.txt',
                    help='Name of the output file. Default is success.txt')
parser.add_argument('-s', '--start-at', dest='start_at', type=int, default=None,
                    help='Need to start at the middle of a directory? Input the file number here. 5 = 5th Image')
parser.add_argument('-dl', '--detect-labels', dest='detect_labels', action="store_true",
                    help='Detect Labels in one image')
parser.add_argument('-ocr', '--ocr', dest='detect_text', action="store_true",
                    help='Detect Text in one image')

args = parser.parse_args()
successFile = open(args.output_file_name,'a')
Path(dirFoundImages).mkdir(parents=True, exist_ok=True)

def getImageFilesFromDirectory():
  arPossibleImages = [fn for fn in os.listdir(imageCompareDir) if fn.split(".")[-1] in accepted_extensions]
  if (intFileIndex != 0):
    arPossibleImages = arPossibleImages[intFileIndex:len(arPossibleImages)]
  return arPossibleImages

def compareFaces(sourceFile, targetFile):
    imageSource=openImageFile(sourceFile)
    imageTarget=openImageFile(os.path.join(imageCompareDir, targetFile))

    response = client.compare_faces(SimilarityThreshold=args.similarity_threshold, SourceImage={'Bytes': imageSource.read()}, TargetImage={'Bytes': imageTarget.read()})
    for faceMatch in response['FaceMatches']:
        global intSuccessMatches
        intSuccessMatches += 1
        similarity = str(faceMatch['Similarity'])
        print(colored('Face from {} & {} are of the same person, with similarity: {}'.format(sourceFile, targetFile, similarity), 'green'))
        successFile.write('Face from {} & {} are of the same person, with similarity: {}\n'.format(sourceFile, targetFile, similarity))
        successFile.flush()
    if not response['FaceMatches']:
      print(colored('No matching person identified in {}'.format(targetFile), 'red'))  
    return len(response['FaceMatches']) 

def getBytesFromImage(photo):
  imgByte = io.BytesIO()
  photo.save(imgByte, format='PNG')
  imgByte = imgByte.getvalue()
  return imgByte

def findFacesByCollection(cropImage, imageName):
  cropImageBytes = getBytesFromImage(cropImage)
  try:
    response=client.search_faces_by_image(CollectionId=args.target_resource,
                        Image={'Bytes': cropImageBytes},
                        FaceMatchThreshold=args.similarity_threshold,
                        MaxFaces=10)
    faceMatches = response['FaceMatches']
    highestSimilarity = 0;
    for match in faceMatches:
      if (match['Similarity'] > highestSimilarity):
        highestSimilarity = match['Similarity']
    if highestSimilarity > 0:
      global intSuccessMatches
      intSuccessMatches += 1
      print(colored('Face from Collection {} & {} are of the same person, with similarity: {}'.format(args.target_resource, imageName, highestSimilarity), 'green'))
      successFile.write('Face from Collection {} & {} are of the same person, with similarity: {}\n'.format(args.target_resource, imageName, highestSimilarity))
      successFile.flush()
      global bFindPerson
      bFindPerson = True
  except client.exceptions.InvalidParameterException as e:
    return;

def openImageFile(filePath):
  try: 
    return open(filePath, 'rb')
  except:
    exit(colored('Cannot open image file: {}'.format(filePath), 'red'))

def detectFacesInImage(photo):  
    arCroppedFaces = []
    with open(os.path.join(imageCompareDir,photo), 'rb') as image:
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])
        faces = [RekognitionFace(face) for face in response['FaceDetails']]
        for face in faces: 
          cropFace = cropBoundingBox(photo, face.bounding_box)
          arCroppedFaces.append(cropFace)
    return arCroppedFaces

def cropBoundingBox(photo, box):
    image = Image.open(os.path.join(imageCompareDir, photo))
    imgWidth, imgHeight = image.size
    left = imgWidth * box['Left']
    top = imgHeight * box['Top']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']
    area = (left, top, left + width, top + height)
    cropFace = image.crop(area)
    #cropFace.show()
    return cropFace

def detectLabels(photo):
    img = openImageFile(photo)
    response = client.detect_labels(Image={'Bytes': img.read()}, MaxLabels=10)

    print('Detected labels for: {}'.format(photo)) 
    for label in response['Labels']:
        print ("Label: {}".format(label['Name']))
        print ("Confidence: {}".format(label['Confidence']))
        print ("Instances:")
        for instance in label['Instances']:
            print ("  Bounding box")
            print ("    Top: {}".format(instance['BoundingBox']['Top']))
            print ("    Left: {}".format(instance['BoundingBox']['Left']))
            print ("    Width: {}".format(instance['BoundingBox']['Width']))
            print ("    Height: {}".format((instance['BoundingBox']['Height'])))
            print ("  Confidence: {}".format(instance['Confidence']))
            print()  
        for parent in label['Parents']:
            print ("Parents:")
            print ("   {}".format(parent['Name']))
        print ("----------")
    return len(response['Labels'])

def detectText(photo):
    img = openImageFile(photo)
    response = client.detect_text(Image={'Bytes': img.read()})
                        
    textDetections=response['TextDetections']
    print ('Detected text\n----------')
    for text in textDetections:
            print('Detected text: {}'.format(text['DetectedText']))
            print('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            print('Id: {}'.format(text['Id']))
            if ('ParentId' in text):
                print ('Parent Id: {}'.format(text['ParentId']))
            print('Type: {}'.format(text['Type']))
    return len(textDetections)


if (args.start_at != None):
  intFileIndex = args.start_at

if (args.detect_labels == False and args.detect_text == False):
  arImageFiles = getImageFilesFromDirectory()
  print('Total Images in Processing: {}'.format(len(arImageFiles)))

for imageName in getImageFilesFromDirectory():
  if ('.' in args.target_resource and args.detect_labels == False and args.detect_text == False):
    compareFaces(args.target_resource, imageName)
  elif ('.' in args.target_resource and args.detect_text == True):
    detectText(args.target_resource)
    print(colored('1 Image Processed', 'green'))
    exit()
  elif ('.' in args.target_resource and args.detect_labels == True):
    detectLabels(args.target_resource)
    print(colored('1 Image Processed', 'green'))
    exit()
  else:
    arCroppedFaces = detectFacesInImage(imageName)
    bFindPerson = False
    for croppedFace in arCroppedFaces:
      findFacesByCollection(croppedFace, imageName)
    if (bFindPerson == False):
      print(colored('No matching person identified in {}'.format(imageName), 'red')) 

print('{} Images Processed'.format(len(arImageFiles)))
print('{} Total Faces Matched'.format(intSuccessMatches))
successFile.close()