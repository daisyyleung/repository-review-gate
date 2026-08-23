create function advance_case(case_id uuid, next_state text)
returns void
language plpgsql
as $$
begin
  update cases set state = next_state where id = case_id;
end;
$$;
