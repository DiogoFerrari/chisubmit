
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

from chisubmit.client import CourseQualifiedApiObject, JSONObject
from chisubmit.client import session
import json

class Grade(JSONObject):
    
    _api_attrs = ('points','grade_component_id')

class StudentTeam(JSONObject):
    
    _api_attrs = ('status',)
    _has_one = {'user': 'student'}

class AssignmentTeam(JSONObject):
    
    _api_attrs = ('extensions_used', 'commit_sha', 'submitted_at', 'assignment_id', 'penalties')
    _has_many = {'grades': 'grades'}
    
    def get_total_penalties(self):
        return sum([p for p in self.penalties.values()])
        
    def get_total_grade(self):
        points = sum([g.points for g in self.grades])
                
        return points + self.get_total_penalties()

class Team(CourseQualifiedApiObject):

    _api_attrs = ('id', 'active', 'course_id')
    _primary_key = 'id'    
    _updatable_attributes = ('active',)
    _has_many = {'students': 'students_teams',
                 'assignments': 'assignments_teams',
                 }
    
    def has_assignment(self, assignment_id):        
        return self.get_assignment(assignment_id) is not None    
    
    def get_assignment(self, assignment_id):
        ats = [at for at in self.assignments if at.assignment_id == assignment_id]
        
        if len(ats) == 1:
            return ats[0]
        else:
            return None        
    
    def add_student(self, student):
        attrs = {'team_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def add_assignment(self, assignment):
        attrs = {'team_id': self.id, 'assignment_id': assignment.id}
        data = json.dumps({'assignments': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def set_assignment_grade(self, assignment_id, grade_component_id, points):
        attrs = {'assignment_id': assignment_id, 'grade_component_id': grade_component_id, 'points': points}
        data = json.dumps({'grades': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def set_assignment_penalties(self, assignment_id, penalties):
        attrs = {'assignment_id': assignment_id, 'penalties': penalties}
        data = json.dumps({'grades': {'penalties': [attrs]}})
        session.put(self.url(), data=data)
