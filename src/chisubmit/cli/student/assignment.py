import click
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_local,\
    create_connection, get_datetime_now_utc
from dateutil.parser import parse
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.assignment import shared_assignment_list


@click.group(name="assignment")
@click.pass_context
def student_assignment(ctx):
    pass


@click.command(name="register")
@click.argument('assignment_id', type=str)
@click.option('--team-name', type=str)
@click.option('--partner', type=str, multiple=True)
@pass_course
@click.pass_context
def student_assignment_register(ctx, course, assignment_id, team_name, partner):
    a = Assignment.from_id(course.id, assignment_id)
        
    a.register(team_name = team_name,
               partners = partner)
    
    return CHISUBMIT_SUCCESS

@click.command(name="show-deadline")
@click.argument('assignment_id', type=str)
@click.option('--utc', is_flag=True)
@pass_course
@click.pass_context
def student_assignment_show_deadline(ctx, course, assignment_id, utc):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    now_utc = get_datetime_now_utc()
    now_local = convert_datetime_to_local(now_utc)

    deadline_utc = assignment.get_deadline()
    deadline_local = convert_datetime_to_local(deadline_utc)

    print assignment.name
    print
    if utc:
        print "      Now (Local): %s" % now_local.isoformat(" ")
        print " Deadline (Local): %s" % deadline_local.isoformat(" ")
        print
        print "        Now (UTC): %s" % now_utc.isoformat(" ")
        print "   Deadline (UTC): %s" % deadline_utc.isoformat(" ")
    else:
        print "      Now: %s" % now_local.isoformat(" ")
        print " Deadline: %s" % deadline_local.isoformat(" ")

    print

    extensions = assignment.extensions_needed(now_utc)

    if extensions == 0:
        diff = deadline_utc - now_utc
    else:
        diff = now_utc - deadline_utc

    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds//60)%60
    seconds = diff.seconds%60

    if extensions == 0:
        print "The deadline has not yet passed"
        print "You have %i days, %i hours, %i minutes, %i seconds left" % (days, hours, minutes, seconds)
    else:
        print "The deadline passed %i days, %i hours, %i minutes, %i seconds ago" % (days, hours, minutes, seconds)
        print "If you submit your assignment now, you will need to use %i extensions" % extensions

    return CHISUBMIT_SUCCESS


def print_commit(commit):
    print "      Commit: %s" % commit.sha
    print "        Date: %s" % commit.committed_date.isoformat(sep=" ")
    print "     Message: %s" % commit.message
    print "      Author: %s <%s>" % (commit.author_name, commit.author_email)        


@click.command(name="submit")
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.argument('commit_sha', type=str)
@click.option('--extensions', type=int, default=0)
@click.option('--force', is_flag=True)
@click.option('--yes', is_flag=True)
@pass_course
@click.pass_context  
def student_assignment_submit(ctx, course, team_id, assignment_id, commit_sha, extensions, force, yes):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)
    
    extensions_requested = extensions
    
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        ctx.exit(CHISUBMIT_FAIL)
    
    commit = conn.get_commit(course, team, commit_sha)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit_sha
        ctx.exit(CHISUBMIT_FAIL)

    response = assignment.submit(team_id, commit_sha, extensions, dry_run=True)

    success = response["success"]
    dry_run = response["dry_run"]

    deadline_utc = parse(response["submission"]["deadline"])
    
    submitted_at_utc = parse(response["submission"]["submitted_at"])
    extensions_needed = response["submission"]["extensions_needed"]
    extensions_requested = response["submission"]["extensions_requested"]    

    extensions_available = response["team"]["extensions_available"]

    deadline_local = convert_datetime_to_local(deadline_utc)
    submitted_at_local = convert_datetime_to_local(submitted_at_utc)
        
    if not success:
        if extensions_needed > extensions_available:
            msg1 = "You do not have enough extensions to submit this assignment."
            msg2 = "You would need %i extensions to submit this assignment at this " \
                   "time, but you only have %i left" % (extensions_needed, extensions_available)
        elif extensions_requested < extensions_needed:
            msg1 = "The number of extensions you have requested is insufficient."
            msg2 = "You need to request %s extensions." % extensions_needed
        elif extensions_requested > extensions_needed:
            msg1 = "The number of extensions you have requested is excessive."
            msg2 = "You only need to request %s extensions." % extensions_needed

        print
        print msg1
        print            
        print "     Deadline (UTC): %s" % deadline_utc.isoformat(sep=" ")
        print "          Now (UTC): %s" % submitted_at_utc.isoformat(sep=" ")
        print 
        print "   Deadline (Local): %s" % deadline_local.isoformat(sep=" ")
        print "        Now (Local): %s" % submitted_at_local.isoformat(sep=" ")
        print 
        print msg2 
        print

        ctx.exit(CHISUBMIT_FAIL)
    else:
        tag_name = assignment.id
        submission_tag = conn.get_submission_tag(course, team, tag_name)
                
        if submission_tag is not None:
            submission_commit = submission_tag.commit
            if not force:
                print        
                print "Submission tag '%s' already exists" % tag_name
                print "It currently points to this commit:"
                print
                print_commit(submission_commit)
                print
                print "If you want to submit again, please use the --force option"
                ctx.exit(CHISUBMIT_FAIL)
            else:
                print
                print "WARNING: Submission tag '%s' already exists and you have requested that it be overwritten" % tag_name
                print "It currently points to this commit:"
                print
                print_commit(submission_commit)
                print
    
        if submission_tag is not None and force:
            msg = "THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (assignment.id, assignment.name)
            
            print "!"*len(msg)
            print msg
            print "!"*len(msg)
            print
            print "If you continue, your submission for %s (%s)" % (assignment.id, assignment.name)
            print "will now point to the following commit:"                
        else:
            print "You are going to make a submission for %s (%s)." % (assignment.id, assignment.name)
            print "The commit you are submitting is the following:"
        print
        print_commit(commit)
        print
        print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
        print 
        print "Are you sure you want to continue? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
        
        if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
            message = "Extensions: %i\n" % extensions_requested
                
            response = assignment.submit(team_id, commit_sha, extensions, dry_run=False)
                
            if submission_tag is None:
                conn.create_submission_tag(course, team, tag_name, message, commit.sha)
            else:
                conn.update_submission_tag(course, team, tag_name, message, commit.sha)
                
            print
            print "Your submission has been completed."
            
        return CHISUBMIT_SUCCESS

student_assignment.add_command(shared_assignment_list)

student_assignment.add_command(student_assignment_register)
student_assignment.add_command(student_assignment_show_deadline)
student_assignment.add_command(student_assignment_submit)
