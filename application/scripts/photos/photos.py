import csv
import random

def create_photo_list():
	#Creates an array of photos for the application to use from a file
    photolist = []
    file = open("application/scripts/photos/central_city_photos.csv","r")    
    csv_reader = csv.reader(file)    
    for line in csv_reader:        
        photo = {}
        photo['PhotoNum'] = line[0]
        photo['creator'] = line[1]
        photo['license'] = line[2]
        photo['latitude'] = float(line[3])
        photo['longitude'] = float(line[4])
        photolist.append(photo)
    return photolist
    
def buildselect(photolist):    
	#Creates an array of ascending numbers to represent a random index number from the photolist
    selection_index = []
    i=0
    for photo in photolist:
        selection_index.append(i)
        i+=1
    return selection_index                

def random_photo(photolist,selection_index):
    #Picks a random photo from the list, then removes it from the selectionindex
    myChoice=random.choice(selection_index)
    return photolist[myChoice]['PhotoNum']
    
def buildPhotoList(photolist, listlength):
	#Uses the previously defined setup functions to build a list of photos with corresponding indexes
    fullindex = buildselect(photolist)
    myList = []
    i=0
    while i<listlength:
        myChoice=random.choice(fullindex)
        photoChoice=photolist[myChoice]
        photo = {}
        photo['PhotoNum'] = photoChoice['PhotoNum']
        photo['creator'] = photoChoice['creator']
        photo['license'] = photoChoice['license']
        photo['latitude'] = photoChoice['latitude']
        photo['longitude'] = photoChoice['longitude']
        myList.append(photo)
        fullindex.remove(myChoice)
        i+=1
    return (myList,buildselect(myList))