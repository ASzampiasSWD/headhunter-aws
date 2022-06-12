#!/usr/bin/python3
import boto3
import argparse
import os
import colorama
from termcolor import colored
from pathlib import Path
from rekognition_objects import RekognitionFace

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


def openImageFile(filePath):
  try: 
    return open(filePath, 'rb')
  except:
    exit(colored('Cannot open image file: {}'.format(filePath), 'yellow'))

def detect_labels_local_file(photo):  
    with open(photo, 'rb') as image:
        #response = client.detect_labels(Image={'Bytes': image.read()})
        client.compare_faces()
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])
        faces = [RekognitionFace(face) for face in response['FaceDetails']]
        print("Detected {} faces.".format(len(faces)))
        print(faces[0].face_id)
        print(faces[0].gender)
        print(faces[0].quality)
        print(faces[0].pose)
        print(faces[0].age_range)        
    #print('Detected labels in ' + photo)    
    #for label in response['Labels']:
    #    print (label['Name'] + ' : ' + str(label['Confidence']))

    return 'nothing'

if (args.start_at != None):
  intFileIndex = args.start_at

arImageFiles = getImageFilesFromDirectory()
print('Total Images in Processing: {}'.format(len(arImageFiles)))

for imageName in getImageFilesFromDirectory():
  compareFaces(args.target_resource, imageName)

print('{} Images Processed'.format(len(arImageFiles)))
print('{} Total Faces Matched'.format(intSuccessMatches))
successFile.close()