#!/usr/bin/python3
import boto3
import argparse
import os
from termcolor import colored

client=boto3.client('rekognition')
accepted_extensions = ["jpg", "png", "jpeg"]
global intFileIndex
intFileIndex = 0
imageCompareDir = os.path.join(os.getcwd())


parser = argparse.ArgumentParser(description='Create a Face Collection for Amazon AWS.')
parser.add_argument('collection_name', type=str,
                    help='name the face collection')
parser.add_argument('-t', '--target_directory', type=str, required=True,
                    help='path of images you want as a collection.')
parser.add_argument('-d', '--delete', dest='is_delete', action="store_true",
                    help='You want to overwrite a pre-existing Collection.')

args = parser.parse_args()
imageCompareDir = args.target_directory

def createCollection(collection_id):
  try: 
    print('Creating collection: {}'.format(collection_id))
    response=client.create_collection(CollectionId=collection_id)
    print('Collection ARN: ' + response['CollectionArn'])
    print(colored('Collection Created', 'green'))
  except Exception: # b more detailed
    print(colored('The FaceIndex Collection tornado already exists. Please delete first.', 'red'))
    exit()

def openImageFile(filePath):
  try: 
    return open(filePath, 'rb')
  except:
    exit(colored('Cannot open image file: {}'.format(filePath), 'red'))

def getImageFilesFromDirectory():
  arPossibleImages = [fn for fn in os.listdir(imageCompareDir) if fn.split(".")[-1] in accepted_extensions]
  if (intFileIndex != 0):
    arPossibleImages = arPossibleImages[intFileIndex:len(arPossibleImages)]
  return arPossibleImages

def deleteCollection(collection_id):
  try:
    client.delete_collection(CollectionId=collection_id)
    print("Deleted Collection: {}".format(collection_id))
  except Exception:
    print("Couldn't Delete Collection {}".format(collection_id))
    exit()

def addFacesToCollection(image,collection_id): 
  photo = openImageFile(os.path.join(imageCompareDir, image))
  response=client.index_faces(CollectionId=collection_id,
                              Image={'Bytes': photo.read()},
                              ExternalImageId=collection_id,
                              MaxFaces=1,
                              QualityFilter="AUTO",
                              DetectionAttributes=['ALL'])
					
  for faceRecord in response['FaceRecords']:
    print(colored('Face ID: ' + faceRecord['Face']['FaceId'], 'green'))
    for unindexedFace in response['UnindexedFaces']:
      print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
      for reason in unindexedFace['Reasons']:
        print('Reason: {}'. format(reason))
    return len(response['FaceRecords'])

def main():
    if (args.is_delete):
      deleteCollection(args.collection_name)
    createCollection(args.collection_name)
    for imageName in getImageFilesFromDirectory():
      addFacesToCollection(imageName, args.collection_name)

if __name__ == "__main__":
    main()