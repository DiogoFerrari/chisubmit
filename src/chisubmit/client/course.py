
#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

import json
from chisubmit.client.assignment import Assignment
from chisubmit.client.team import Team
from chisubmit.client import session, ApiObject, JSONObject
from chisubmit.client.user import User

class CourseStudent(JSONObject):
    
    _api_attrs = ('dropped', 'repo_info')
    _has_one = {'user': 'student'}

class CourseInstructor(JSONObject):
    
    _api_attrs = ('repo_info',)
    _has_one = {'user': 'instructor'}

class CourseGrader(JSONObject):
    
    _api_attrs = ('repo_info',)
    _has_one = {'user': 'grader'}


class Course(ApiObject):

    _api_attrs = ('id', 'name', 'options')
    _primary_key = 'id'    
    _updatable_attributes = ['name']
    
    _has_many = {'instructors': 'courses_instructors',
                 'graders': 'courses_graders',
                 'students': 'courses_students',
                 'assignments': 'assignments',
                 'teams': 'teams'}

    def add_student(self, student):
        attrs = {'course_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)

    def add_team(self, team):
        attrs = {'course_id': self.id, 'team_id': team.id}
        data = json.dumps({'teams': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)

    def add_grader(self, grader):
        attrs = {'course_id': self.id, 'grader_id': grader.id}
        data = json.dumps({'graders': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)
            
    def add_instructor(self, instructor):
        attrs = {'course_id': self.id, 'instructor_id': instructor.id}
        data = json.dumps({'instructors': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)        
        
    def set_option(self, name, value):
        attrs = {'name': name, 'value': value}
        data = json.dumps({'options': {'update': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)        

    def __set_repo_option(self, user_type, user_id, name, value):
        attrs = {'name': name, 'value': value}

        data = {"%ss" % user_type: 
                {
                 "update": [
                            {"%s_id" % user_type: user_id,
                             "repo_info": [attrs]}
                           ]
                }
               }        
        data = json.dumps(data)
        session.put('courses/%s' % (self.id), data=data) 
 
    def set_instructor_repo_option(self, instructor_id, name, value):
        self.__set_repo_option("instructor", instructor_id, name, value)

    def set_grader_repo_option(self, grader_id, name, value):
        self.__set_repo_option("grader", grader_id, name, value)

    def set_student_repo_option(self, student_id, name, value):
        self.__set_repo_option("student", student_id, name, value)
 
    def get_assignment(self, assignment_id):
        return Assignment.from_id(self.id, assignment_id)

    def get_team(self, team_id):
        return Team.from_id(self.id, team_id) 

    def search_team(self, search_term):
        teams = []
        for t in self.teams.values():
            fields = [t.id, t.private_name]
            for s in t.students:
                fields += [s.first_name, s.last_name, s.github_id]

            for v in fields:
                if search_term.lower() in v.lower():
                    teams.append(t)
                    break

        return teams
