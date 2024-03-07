#### This repo is a project management tool similar to Trello or Asana using Django REST Framework.
I used a Test Driven Development approach in this project.

## Database Schema:

1. **User**:
   - id
   - username
   - email
   - password (hashed)
   - date_joined

2. **Team**:
   - id
   - name
   - description
   - public_edit
   - privacy_edit

3. **TeamMember**
   - id
   - user (Foreign Key to User)
   - team (Foreign Key to Team)
   - is_admin

4. **Project**:
   - id
   - name
   - description
   - team (Foreign Key to Team)
   - created_at
   - deadline

5. **Task**:
   - id
   - title
   - description
   - project (Foreign Key to Project)
   - assigned_to (Foreign Key to TeamMember)
   - created_by (Foreign Key to TeamMember)
   - created_at
   - due_date
   - status (e.g., To Do, In Progress, Done)

## Features:

1. **User Management:**

   - User registration
   - User authentication (using TokenAuthentication)
   - User profile management (update profile, change password, reset password)

2. **Team Management:**

   - Create a team
   - Update team details
   - Delete teams with admin role only
   - View all teams a user is a member of
   - Add members to the team
   - Remove members from the team
   - Assign roles to the team members (admin, member)

3. **Project Management:**

   > ***Each project is assigned to a team and only team admins can create, update or delete the project.***
   - Create a project within a team
   - View all projects a user is involved in
   - Update project details
   - Set deadlines for projects
   - Delete a project

4. **Task Management:**

   - Create tasks within a project
   - Assign tasks to team members
   - Set due dates for tasks
   - Update task status (e.g., To Do, In Progress, Done)
   - Comment on tasks (TODO)
