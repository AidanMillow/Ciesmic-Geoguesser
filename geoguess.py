import math, random
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
app = Flask(__name__)

@app.route('/geoguess')
def init():
	return redirect(url_for('guess_photo',PhotoNo = random_photo()))

@app.route('/geoguess/guess/<int:PhotoNo>')
def guess_photo(PhotoNo):
    return render_template('guess.html', photo = PhotoNo, difference=-1)

@app.route('/geoguess/check/<int:PhotoNo>', methods =['POST', 'GET'])
def check_guess(PhotoNo):
    if request.method == 'POST':
		if PhotoNo == 55233:
			latitude = -43.5329
			longitude = 172.639
		if PhotoNo == 64422:
			latitude = -43.5396
			longitude = 172.6373
		if PhotoNo == 81851:
			latitude = -43.5321
			longitude = 172.6374
		if PhotoNo == 135054:
			latitude = -43.5306
			longitude = 172.631
		if PhotoNo == 149953:
			latitude = -43.5312
			longitude = 172.6413
		if PhotoNo == 173308:
			latitude = -43.5316
			longitude = 172.6323
		if PhotoNo == 175357:
			latitude = -43.5322
			longitude = 172.6391
		if PhotoNo == 175561:
			latitude = -43.5312
			longitude = 172.6394
		if PhotoNo == 176751:
			latitude =-43.5322
			longitude =172.6372
		Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
		Printdifference='{0:.3f}'.format(Guessdifference)
		return render_template('guess.html', photo = random_photo(), difference = Guessdifference, Printdiff = Printdifference)
def random_photo():
	selection=[55233,64422,81851,135054,149953,173308,175357,175561,176751]
	myChoice=random.choice(selection)
	selection.remove(myChoice)
	return myChoice
	

if __name__ == '__main__':
	app.run(debug=True)