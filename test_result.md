#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "DocXL AI - MIGRATED to Supabase. SaaS app converting PDFs/images to Excel. Supabase Auth + PostgreSQL + Storage. AI extraction via Python emergentintegrations."

backend:
  - task: "Health Check API"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "GET /api/health - returns {status:ok, backend:supabase}"
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Health check passed - Supabase backend confirmed. Returns correct status and backend type."

  - task: "User Registration (Supabase Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "POST /api/auth/register - supabase.auth.admin.createUser with email_confirm:true. Auto-creates profile via DB trigger."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: User registration successful. Creates user with email test_iwgvc3j3@docxl.com, returns user object with plan and credits."

  - task: "User Login (Supabase Auth)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "POST /api/auth/login - supabase.auth.signInWithPassword. Returns access_token + refresh_token."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Login successful. Returns access_token and user data with plan (free) and credits (5)."

  - task: "Get Current User"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "GET /api/auth/me - verifies Supabase JWT, fetches profile from profiles table."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Get user info successful. Returns complete user profile with ID, email, plan, and credits."

  - task: "File Upload (Supabase Storage)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "POST /api/upload - uploads to Supabase Storage uploads bucket + inserts DB record."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: File upload successful. Uploaded 800x600 PNG with financial data, returns upload ID and status 'uploaded'."

  - task: "AI Process"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "POST /api/process - downloads from Supabase Storage, calls Python AI script, saves to results table, deducts credits."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: AI processing successful. Extracted 5 rows from invoice image, document_type: invoice, confidence: 0.85. Credits properly deducted."

  - task: "Get Result"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "GET /api/result/:id - queries results table with uploads JOIN."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Get result successful. Returns extracted data with 5 rows, upload_id, and file_name."

  - task: "Export Excel"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "GET /api/export/excel/:id - generates xlsx from Supabase data."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Excel export successful. Returns proper xlsx file (6820 bytes) with correct content-type."

  - task: "List Uploads"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "GET /api/uploads - queries Supabase uploads table."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Get uploads successful. Returns user uploads list, verified upload status as 'completed'."

  - task: "Delete File"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "DELETE /api/file/:id - deletes from Supabase Storage + DB."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Delete file successful. File removed from both Supabase Storage and database, verified by checking uploads list."

  - task: "Update Result"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
        - agent: "main"
        - comment: "PUT /api/result/:id - updates edited_json in results table."
        - working: true
        - agent: "testing"
        - comment: "✅ TESTED: Update result successful. Edited rows data saved properly, returns success message."

metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 3
  run_ui: false

test_plan:
  current_focus:
    - "All backend endpoints - Supabase migration verification"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
    - message: "COMPLETE SUPABASE MIGRATION. All APIs use Supabase (Auth + Storage + PostgreSQL). No MongoDB. Auth uses Supabase tokens. Register via admin.createUser, login via signInWithPassword. Files in Supabase Storage uploads bucket. Read /app/image_testing.md for image rules. Python script at /app/scripts/extract.py. EMERGENT_LLM_KEY in .env. Supabase credentials in .env."
    - agent: "testing"
    - message: "✅ BACKEND TESTING COMPLETE: All 11 backend endpoints tested successfully (13/13 tests passed). Supabase migration fully verified. Health check confirms Supabase backend. Auth flow working (register/login/me). File upload to Supabase Storage working. AI processing extracts data correctly and deducts credits. Excel export generates proper xlsx files. CRUD operations on uploads/results working. All endpoints use proper Supabase authentication. No critical issues found."

