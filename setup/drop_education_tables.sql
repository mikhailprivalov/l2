-- Remove leftover education module tables/FKs that block clients_card deletes.
-- Safe to re-run. Review before executing on production.

BEGIN;

-- Child / linking tables first (also covered by CASCADE below).
DROP TABLE IF EXISTS education_entranceexam CASCADE;
DROP TABLE IF EXISTS education_achievement CASCADE;
DROP TABLE IF EXISTS education_cardspecialrights CASCADE;
DROP TABLE IF EXISTS education_applicationeducation CASCADE;
DROP TABLE IF EXISTS education_documenteducation CASCADE;
DROP TABLE IF EXISTS education_educationspeciality CASCADE;
DROP TABLE IF EXISTS education_logupdatemmis CASCADE;
DROP TABLE IF EXISTS education_subjects CASCADE;
DROP TABLE IF EXISTS education_examtype CASCADE;
DROP TABLE IF EXISTS education_formeducation CASCADE;
DROP TABLE IF EXISTS education_faculties CASCADE;
DROP TABLE IF EXISTS education_achievementtype CASCADE;
DROP TABLE IF EXISTS education_applicationsourceeducation CASCADE;
DROP TABLE IF EXISTS education_specialrights CASCADE;
DROP TABLE IF EXISTS education_specialrightstype CASCADE;
DROP TABLE IF EXISTS education_documenttypeeducation CASCADE;
DROP TABLE IF EXISTS education_typeeducation CASCADE;
DROP TABLE IF EXISTS education_leveleducation CASCADE;
DROP TABLE IF EXISTS education_institutiontitle CASCADE;
DROP TABLE IF EXISTS education_typeinstitutioneducation CASCADE;

-- Catch any remaining education_* tables (renames / later migrations).
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename LIKE 'education_%'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', r.tablename);
    END LOOP;
END $$;

DELETE FROM django_migrations WHERE app = 'education';

COMMIT;

-- Optional checks:
-- SELECT to_regclass('public.education_entranceexam');
-- SELECT COUNT(*) FROM django_migrations WHERE app = 'education';
