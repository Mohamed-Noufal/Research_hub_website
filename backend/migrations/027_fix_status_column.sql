-- Migration 027: Fix agent_task_states status column length
-- The status 'completed_with_errors' is 21 chars, exceeds VARCHAR(20)

ALTER TABLE agent_task_states 
    DROP CONSTRAINT IF EXISTS agent_task_states_status_check;

ALTER TABLE agent_task_states 
    ALTER COLUMN status TYPE VARCHAR(30);

ALTER TABLE agent_task_states 
    ADD CONSTRAINT agent_task_states_status_check 
    CHECK (status IN ('pending', 'running', 'completed', 'completed_with_errors', 'failed', 'paused'));
