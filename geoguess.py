import math
from random import randint
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
app = Flask(__name__)

photolist = [{'PhotoNum':55233,'latitude':-43.5329,'longitude':172.639},
			{'PhotoNum':64422,'latitude':-43.5396,'longitude':172.6373},
			{'PhotoNum':81851,'latitude':-43.5321,'longitude':172.6374},
			{'PhotoNum':135054, 'latitude':-43.5306, 'longitude':172.631},
			{'PhotoNum':149953, 'latitude':-43.5312, 'longitude':172.6413},
			{'PhotoNum':173308, 'latitude':-43.5316, 'longitude':172.6323},
			{'PhotoNum':175357, 'latitude':-43.5322, 'longitude':172.6391},
			{'PhotoNum':175561, 'latitude':-43.5312, 'longitude':172.6394},
			{'PhotoNum':176751, 'latitude':-43.5322, 'longitude':172.6372}]

@app.route('/geoguess')
def init():
	return redirect(url_for('guess_photo',PhotoNo = 55233))

@app.route('/geoguess/guess/<int:PhotoNo>')
def guess_photo(PhotoNo):
    return render_template('guess.html', photo = PhotoNo, difference=-1)

@app.route('/geoguess/check/<int:PhotoNo>', methods =['POST', 'GET'])
def check_guess(PhotoNo):
    if request.method == 'POST':
		NextPhoto = randint(0,photolist.len-1)
		for photo in photolist:
			if PhotoNo == photo['PhotoNum']:
				latitude = photo['latitude']
				longitude = photo['longitude']
			elif randint(0,9) >= 7:
				NextPhoto = photo['PhotoNum']
		Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))
		Guessdifference=float("%.3f" % Guessdifference)
		return render_template('guess.html', photo = NextPhoto, difference = Guessdifference)
    else:
		return redirect(url_for('guess_photo',PhotoNo = 55233))


if __name__ == '__main__':
	app.run(debug=True)