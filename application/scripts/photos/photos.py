import csv
import random

def create_photo_list():
    photolist = []
    file = open("application/scripts/photos/central_city.csv","r")    
    csv_reader = csv.reader(file)    
    for line in csv_reader:        
        photo = {}
        photo['PhotoNum'] = line[0]
        photo['latitude'] = float(line[1])
        photo['longitude'] = float(line[2])
        photolist.append(photo)
    return photolist
    
def buildselect(photolist):    
    selection_index = []
    i=0
    for photo in photolist:
        selection_index.append(i)
        i+=1
    return selection_index                

def random_photo(photolist,selection_index):
	#picks a random photo from the list, then removes it from the selectionindex
	myChoice=random.choice(selection_index)
	return photolist[myChoice]['PhotoNum']