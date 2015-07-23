from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_ASSIGNMENTS, COURSE2_ASSIGNMENTS,\
    COURSE1_TEAMS, COURSE1_TEAM_MEMBERS
from chisubmit.client.exceptions import BadRequestException
from chisubmit.backend.api.models import Course, Assignment, TeamMember,\
    Registration

class TeamTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'complete_course1', 'course1_teams']
    
    def test_get_teams(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        teams = course.get_teams()
        
        self.assertEquals(len(teams), len(COURSE1_TEAMS))
        self.assertItemsEqual([t.name for t in teams], COURSE1_TEAMS)
        
    def test_get_team(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for team_name in COURSE1_TEAMS:
            team = course.get_team(team_name)
            
            self.assertEquals(team.name, team_name)
            
    def test_create_team(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        team = course.create_team(name = "student2-student3",
                                  extensions = 2,
                                  active = False)
        self.assertEquals(team.name, "student2-student3")
        self.assertEquals(team.extensions, 2)
        self.assertEquals(team.active, False)
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        team_obj = course_obj.get_team("student2-student3")
        self.assertIsNotNone(team_obj, "Team was not added to database")
            
        self.assertEquals(team_obj.name, "student2-student3")                  
        self.assertEquals(team_obj.extensions, 2)                  
        self.assertEquals(team_obj.active, False)                  
                    
class TeamMemberTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'complete_course1', 'course1_teams']    
    
    def test_get_team_members(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            team_members = team.get_team_members()
            
            self.assertEquals(len(team_members), len(COURSE1_TEAM_MEMBERS[t]))
            self.assertItemsEqual([tm.username for tm in team_members], COURSE1_TEAM_MEMBERS[t])
            self.assertItemsEqual([tm.student.user.username for tm in team_members], COURSE1_TEAM_MEMBERS[t])
        
    def test_get_team_member(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            
            for tm in COURSE1_TEAM_MEMBERS[t]:
                team_member = team.get_team_member(tm)
                
                self.assertEqual(team_member.username, tm)
                self.assertEqual(team_member.student.user.username, tm)
                self.assertEqual(team_member.confirmed, True)
                
    
    def test_create_team_with_team_members(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        team = course.create_team(name = "student2-student3",
                                  extensions = 2,
                                  active = False)
        self.assertEquals(team.name, "student2-student3")
        self.assertEquals(team.extensions, 2)
        self.assertEquals(team.active, False)
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        team_obj = course_obj.get_team("student2-student3")
        self.assertIsNotNone(team_obj, "Team was not added to database")
            
        self.assertEquals(team_obj.name, "student2-student3")                  
        self.assertEquals(team_obj.extensions, 2)                  
        self.assertEquals(team_obj.active, False)
              
        team_member = team.add_team_member("student2", confirmed = False)
        self.assertEqual(team_member.username, "student2")
        self.assertEqual(team_member.student.user.username, "student2")
        self.assertEqual(team_member.confirmed, False)
                
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student2")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student2")
        self.assertEqual(team_member_obj.confirmed, False)
        
        team.add_team_member("student3", confirmed = True)
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student3")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student3")
        self.assertEqual(team_member_obj.confirmed, True)

        team_members = team.get_team_members()
        
        self.assertEquals(len(team_members), 2)
        self.assertItemsEqual([tm.username for tm in team_members], ["student2","student3"])
        self.assertItemsEqual([tm.student.user.username for tm in team_members], ["student2","student3"])        
        
class RegistrationTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'complete_course1', 'course1_teams', 'course1_pa1_registrations']    
    
    def test_get_registrations(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registrations = team.get_assignment_registrations()
            
            self.assertEquals(len(registrations), 1)
            self.assertItemsEqual([r.assignment_id for r in registrations], ["pa1"])
            self.assertItemsEqual([r.assignment.assignment_id for r in registrations], ["pa1"])
        
    def test_get_registration(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")

            self.assertEqual(registration.assignment_id, "pa1")
            self.assertEqual(registration.assignment.assignment_id, "pa1")
            self.assertEqual(registration.grader_username, None)
            self.assertEqual(registration.grader, None)
            
    def test_create_registration(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.add_assignment_registration("pa2")

            self.assertEqual(registration.assignment_id, "pa2")
            self.assertEqual(registration.assignment.assignment_id, "pa2")
            self.assertEqual(registration.grader_username, None)
            self.assertEqual(registration.grader, None)   
            
            registration_objs = Registration.objects.filter(team__name = t, assignment__assignment_id = "pa2")
            self.assertEquals(len(registration_objs), 1)
            registration_obj = registration_objs[0]
            self.assertEqual(registration_obj.team.name, t)
            self.assertEqual(registration_obj.assignment.assignment_id, "pa2")
            self.assertIsNone(registration_obj.grader)            
            
            registrations = team.get_assignment_registrations()
            
            self.assertEquals(len(registrations), 2)
            self.assertItemsEqual([r.assignment_id for r in registrations], ["pa1", "pa2"])
            self.assertItemsEqual([r.assignment.assignment_id for r in registrations], ["pa1", "pa2"])            
                