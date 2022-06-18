#!/usr/bin/python3
import boto3
import argparse
import os
import colorama
from termcolor import colored
from pathlib import Path
from rekognition_objects import RekognitionFace
import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ExifTags, ImageColor
import io

global intFileIndex
intFileIndex = 0
global dirFoundImages
dirFoundImages = './Found_Images'
accepted_extensions = ["jpg", "png", "jpeg"]
imageCompareDir = os.path.join(os.getcwd(), 'Images')
global intSuccessMatches
intSuccessMatches = 0
colorama.init()
client=boto3.client('rekognition')
maxFaces=3

parser = argparse.ArgumentParser(description='Find face matches from one image.')
parser.add_argument('target_resource', type=str,
                    help='path of the person image you want found')
parser.add_argument('-st', '--similarity-threshold', dest='similarity_threshold', type=int,
                    default=70, help='Minimum threshold allowed for face matches. Default is 70.')
parser.add_argument('-c', '--compare-directory', dest='compare_directory', type=str, default=None,
                    help='Is there another folder you would like to get comparision images from? Default is Current_Directory/Images/')
parser.add_argument('-o', '--output-file', dest='output_file_name', type=str, default='success.txt',
                    help='Name of the output file. Default is success.txt')
parser.add_argument('-s', '--start-at', dest='start_at', type=int, default=None,
                    help='Need to start at the middle of a directory? Input the file number here. 5 = 5th Image')

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


def findFacesByCollection(image):
  photo = openImageFile(os.path.join(imageCompareDir, image))
  print('AMANDAAAA: ' + image)
  response=client.search_faces_by_image(CollectionId=args.target_resource,
                        Image={'Bytes': photo.read()},
                        FaceMatchThreshold=args.similarity_threshold,
                        MaxFaces=10)
  image_face = RekognitionFace({
    'BoundingBox': response['SearchedFaceBoundingBox'],
    'Confidence': response['SearchedFaceConfidence']
  })
  print(response['SearchedFaceBoundingBox'])
  exit()
  collection_faces = [RekognitionFace(face['Face']) for face in response['FaceMatches']]
  #print("Found {} faces in the collection that match the largest face in {}".format(len(collection_faces), image))
  #print(response)
  faceMatches=response['FaceMatches']
  highestSimilarity = 0;
  for match in faceMatches:
    if (match['Similarity'] > highestSimilarity):
      highestSimilarity = match['Similarity']
  if highestSimilarity > 0:
    global intSuccessMatches
    intSuccessMatches += 1
    print(colored('Face from Collection {} & {} are of the same person, with similarity: {}'.format(args.target_resource, image, highestSimilarity), 'green'))
    successFile.write('Face from Collection {} & {} are of the same person, with similarity: {}\n'.format(args.target_resource, image, highestSimilarity))
    successFile.flush()

def openImageFile(filePath):
  try: 
    return open(filePath, 'rb')
  except:
    exit(colored('Cannot open image file: {}'.format(filePath), 'yellow'))

def detect_labels_local_file(photo):  
    with open(os.path.join(imageCompareDir,photo), 'rb') as image:
        #response = client.detect_labels(Image={'Bytes': image.read()})
        #client.compare_faces()
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])
        print('GATOR18: ' + str(response))
        faces = [RekognitionFace(face) for face in response['FaceDetails']]
        print(faces[0].face_id)
        print(faces[0])
        print("Detected {} faces.".format(len(faces)))
    img = Image.open(os.path.join(imageCompareDir,photo))
    draw = ImageDraw.Draw(img)  
    imgWidth, imgHeight = img.size

    box = faces[0].bounding_box
    left = imgWidth * box['Left']
    top = imgHeight * box['Top']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']

    points = (
            (left,top),
            (left + width, top),
            (left + width, top + height),
            (left , top + height),
            (left, top)

        )
    #draw.line(points, fill='#00d400', width=2)
    #draw.rectangle([left,top, left + width, top + height], outline='#00d400')
    #img.crop(points)
    image2 = Image.open(open(os.path.join(imageCompareDir,photo), 'rb'))
    area = (left, top, left + width, top + height)
    face = image2.crop(area)
    face.show()

    return 'nothing'

def cropBoundingBox():
    #{'Width': 0.1308685839176178, 'Height': 0.26206353306770325, 'Left': 0.5228204727172852, 'Top': 0.17819029092788696}
    width =0.1308685839176178
    height=0.26206353306770325
    left=0.5228204727172852
    top=0.17819029092788696
    filePath = os.path.join(imageCompareDir,'ElonCowboyHatSunglasses.jpeg')
    img = Image.open(filePath)
    print(filePath)
    cropped = img.crop( ( left, top, left + width, top + height ) ) 
    cropped.show()
    #plt.imshow(cropped_image)
    #cv2.imwrite(img, cropped_image)



if (args.start_at != None):
  intFileIndex = args.start_at

arImageFiles = getImageFilesFromDirectory()
print('Total Images in Processing: {}'.format(len(arImageFiles)))

for imageName in getImageFilesFromDirectory():
  if ('.' in args.target_resource):
    compareFaces(args.target_resource, imageName)
    cropBoundingBox()
  else:
    detect_labels_local_file(imageName)
    #cropBoundingBox()
    #detect_labels_local_file(imageName)
    #findFacesByCollection(imageName)

print('{} Images Processed'.format(len(arImageFiles)))
print('{} Total Faces Matched'.format(intSuccessMatches))
successFile.close()