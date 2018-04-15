# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import Config as config

import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import *

import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

def kerberos_to_entry_number(kerberos):
	return "20" + kerberos[3:5] + kerberos[:3].upper() + kerberos[5:]

# Create your views here.
def index(request):
	if request.method=='POST':
		return redirect(config.authLinkPart1 + config.CLIENT_ID + config.authLinkPart2)
	return render(request, 'myapp/index.html')

def authenticate(request):
	PostData = {'client_id':config.CLIENT_ID,
	'client_secret':config.CLIENT_SECRET,
	'grant_type':config.AUTHORIZATION_CODE,
	'code':request.GET.get('code')}

	r = requests.post(config.OauthTokenURL, PostData,verify=config.certiPath)
	a = r.json()
	access_token = a['access_token']
	PostData2 = {
		'access_token':access_token
	}
	r1 = requests.post(config.ResourceURL, PostData2,verify=config.certiPath)
	b = r1.json()

	if User.objects.filter(username = (b['uniqueiitdid']).lower()).exists():
		myUser = User.objects.get(username = (b['uniqueiitdid']).lower())
		login(request, myUser)
		return redirect('/profile')
	else:
            return redirect('/')
            #return render(request, 'myapp/index.html', {"auth":"User cannot be logged in"})	   

@login_required()
def profile(request):
	# add image field edit
	u = request.user
	UsrObj = Student(name=u.student.name, department=u.student.department,
			DP=u.student.DP,phone=u.student.phone,email=u.student.email,
			oneliner=u.student.oneliner,genPic1=u.student.genPic1,genPic2=u.student.genPic2)
	if request.method=='GET':
		context={"user":UsrObj}
		return render(request, 'myapp/profile.html',context)
	# print int(request.FILES.get('dp').size)<6000000
	if(request.FILES.get('dp')!=None and int(request.FILES.get('dp').size)<6000000):
		# Get the picture
		picture = request.FILES.get('dp')
		# check extension
		if not (picture.name.lower().endswith(('.png', '.jpg', '.jpeg'))):
			return render(request , 'myapp/profile.html', {"user":UsrObj ,"image": "Image should be in .png, .jpg or .jpeg format"})
		picture.name = u.username + ".jpg"
		u.student.DP = picture 

	if(request.FILES.get('genPic1')!=None and int(request.FILES.get('genPic1').size)<6000000):
		u.student.genPic1 = request.FILES.get('genPic1')
		if not (u.student.genPic1.name.lower().endswith(('.png', '.jpg', '.jpeg'))):
			return render(request , 'myapp/profile.html', {"user":UsrObj ,"image": "Image should be in .png, .jpg or .jpeg format"})
		u.student.genPic1.name = u.username + "_1.jpg"
		
	if(request.FILES.get('genPic2')!=None and int(request.FILES.get('genPic2').size)<6000000):
		u.student.genPic2 = request.FILES.get('genPic2')
		if not (u.student.genPic2.name.lower().endswith(('.png', '.jpg', '.jpeg'))):
			return render(request , 'myapp/profile.html', {"user":UsrObj ,"image": "Image should be in .png, .jpg or .jpeg format"})
		u.student.genPic2.name = u.username + "_2.jpg"
	
	u.student.name = request.POST.get('name')
	if len(u.student.name) == 0:
		return render(request , 'myapp/profile.html', {"user":UsrObj ,"name": "Name cannot be empty"})
		
	# Phone email and oneliner can be empty if the user does not wish to specify.
	u.student.phone = request.POST.get('phone')
	u.student.email = request.POST.get('email')
	u.student.oneliner = request.POST.get('oneliner')
	u.student.save()
	return redirect('/profile')



@login_required
def answerMyself(request):
	u = request.user
	if request.method=='GET':
		GenQuestions = GenQuestion.objects.all()
		AnswersDisplay = u.student.AnswersAboutMyself
		gen_GenQuestions = []
		for q in GenQuestions:
			gen_GenQuestions.append([q.id,q.question,""])
			if (AnswersDisplay.has_key(str(q.id))):
				gen_GenQuestions[-1][-1] = AnswersDisplay[str(q.id)]
		context={"genQuestions":gen_GenQuestions}
		return render(request, 'myapp/answers.html',context)
	# print request.POST.getlist('answer[]')
	for i in range(len(request.POST.getlist('answer[]'))):
		if GenQuestion.objects.filter(id = request.POST.getlist('id[]')[i]).exists():
			u.student.AnswersAboutMyself[request.POST.getlist('id[]')[i]] = request.POST.getlist('answer[]')[i]
		else:
			return redirect('/answer')
		u.student.save()
	return redirect('/answer')
	
@login_required()
def poll(request):
	u = request.user

    # department user should be from same year
	if request.method=='GET':
		users_all = User.objects.filter(is_superuser=False).order_by('username')
		dept_users=[]
		enum_to_name = {}
		for i in users_all:
			enum_to_name[i.username] = i.student.name
			if i.student.department==u.student.department:
				if i.username[:4] == u.username[:4]:
					#also add an year check
					dept_users.append(i)

		#print enum_to_name
		allPolls = Poll.objects.filter(department="all")
		deptPolls = Poll.objects.filter(department=u.student.department)
                
		VotesDisplay = u.student.VotesIHaveGiven
		gen_allPolls=[]
		gen_deptPolls=[]
		for p in allPolls:
			gen_allPolls.append([p.id,p.poll,""])
			if (VotesDisplay.has_key(str(p.id))):
				gen_allPolls[-1][-1]=VotesDisplay[str(p.id)]
		for p in deptPolls:
			gen_deptPolls.append([p.id,p.poll,""])
			if (VotesDisplay.has_key(str(p.id))):
				gen_deptPolls[-1][-1]=VotesDisplay[str(p.id)]
		# add a name field to display I dont know how to get name
		# straight away
    	# print gen_deptPolls
		for i in range(len(gen_deptPolls)):
			name = enum_to_name.get(gen_deptPolls[i][-1], "")
			#if name != -1:
			gen_deptPolls[i].append(name)

		context={"allPolls":gen_allPolls, "deptPolls":gen_deptPolls,"users":users_all,"deptUsers":dept_users}
		return render(request, 'myapp/poll.html',context)

	# if POST request 
	# print request.POST.getlist('entrynumber[]')
	for i in range(len(request.POST.getlist('entrynumber[]'))):
		fetchPoll = ""
		if Poll.objects.filter(id = request.POST.getlist('id[]')[i]).exists():
			fetchPoll = Poll.objects.get(id = request.POST.getlist('id[]')[i])
		else:
			return redirect("/poll")
		if (u.student.VotesIHaveGiven.has_key(request.POST.getlist('id[]')[i])):
			OldVotePresent = u.student.VotesIHaveGiven[request.POST.getlist('id[]')[i]]
			fetchPoll.votes[OldVotePresent] = fetchPoll.votes[OldVotePresent] - 1	
		
		lowerEntry = (request.POST.getlist('entrynumber[]')[i]).lower()
		if(fetchPoll.votes.has_key(lowerEntry)):
			if ((lowerEntry != u.username.lower())):
				fetchPoll.votes[lowerEntry] = fetchPoll.votes[lowerEntry] + 1	
			else:
				return redirect("/poll")
		else:
			# A not found check for poll and Cannot vote oneself
			print(lowerEntry)
			print(User.objects.filter(username = lowerEntry).exists())
			print(u.username.lower())
			if (User.objects.filter(username = lowerEntry).exists() and (lowerEntry != u.username.lower())):
				toVoteDepartment = (User.objects.get(username=lowerEntry)).student.department
				if (((fetchPoll.department.lower() == "all") or (fetchPoll.department.lower() == toVoteDepartment.lower())) and (lowerEntry[0:4] == u.username[0:4])):		
					fetchPoll.votes[lowerEntry] = 1
				else:
					return redirect("/poll")		
			else:
				return redirect("/poll")
		u.student.VotesIHaveGiven[request.POST.getlist('id[]')[i]] = lowerEntry		
		fetchPoll.save()
		u.student.save()
	return redirect("/poll")
		
@login_required()
def comment(request):
	u = request.user
	users_all = User.objects.filter(is_superuser=False).order_by('username') 
		#we pass this to display options, remove self user
	myComments = u.student.CommentsIWrite
	gen_comments = []
	for c in myComments:
		tmpName=c["forWhom"]
		if User.objects.filter(username = c["forWhom"]).exists():
			tmpName=User.objects.get(username=c["forWhom"]).student.name
		gen_comments.append([c["comment"],c["forWhom"],tmpName])
	context={"comments":gen_comments,"users":users_all}
	if request.method=='GET':
		return render(request, 'myapp/comment.html',context)
	for i in range(len(request.POST.getlist('forWhom[]'))):
		lowerEntry = (request.POST.getlist('forWhom[]')[i]).lower()
		for c in u.student.CommentsIWrite:
			if c["forWhom"]==lowerEntry: #updating an already written message
				c["comment"]=request.POST.getlist('val[]')[i]
				# A not found check for the user
				if (User.objects.filter(username = lowerEntry).exists() and (u.username.lower() != lowerEntry)):
					u_new = User.objects.get(username=lowerEntry) 
				else:
					return redirect('/comment')
				for c_new in u_new.student.CommentsIGet:
					if c_new["fromWhom"]==u.username:
						c_new["comment"]=request.POST.getlist('val[]')[i]
						break
				u_new.student.save()
				break
		else:
			u.student.CommentsIWrite.append({"comment":request.POST.getlist('val[]')[i],"forWhom":lowerEntry})
			# A not found check of user and I cant comment for myself
			if (u.username.lower() == lowerEntry):
				return render(request, 'myapp/comment.html', {"comments":gen_comments,"users":users_all, "comment": "You can't comment for yourself :)"})
			if (User.objects.filter(username = lowerEntry).exists()):
				u_new = User.objects.get(username=lowerEntry)
			else:
				print User.objects.filter(username = lowerEntry).exists()
				return redirect('/comment')
			u_new.student.CommentsIGet.append({"comment":request.POST.getlist('val[]')[i],"fromWhom":u.username,"displayInPdf":"True"})
			u_new.student.save()
		u.student.save()
	return redirect('/comment')

@login_required()
def otherComment(request):
	u = request.user
	if request.method=='GET':
		CommentsIGet = u.student.CommentsIGet
		gen_comments=[]
		for c in CommentsIGet:
			tmpName=c["fromWhom"]
			if User.objects.filter(username = c["fromWhom"]).exists():
				tmpName=User.objects.get(username=c["fromWhom"]).student.name
			gen_comments.append([c["comment"],c["fromWhom"],tmpName,c["displayInPdf"]])
		context={"comments":gen_comments}
		return render(request, 'myapp/otherComment.html',context)
	for i in range(len(request.POST.getlist('fromWhom[]'))):
		lowerEntry = (request.POST.getlist('fromWhom[]')[i]).lower()
		for c in u.student.CommentsIGet:
			if c["fromWhom"]==lowerEntry:
				c["displayInPdf"]=request.POST.getlist('val[]')[i]
				break
		u.student.save()
	return redirect('/otherComment')



def userlogout(request):
	logout(request)
	return redirect("/")
	
