CREATE OR REPLACE FUNCTION public.obter_associados_por_escopo(p_escopo_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_matricula TEXT;
    v_json JSON;
BEGIN
    -- 1. Buscar a matrícula do escopo
    SELECT e.matricula
    INTO v_matricula
    FROM escopo e
    WHERE e.id = p_escopo_id;

    -- 2. Buscar todos os associados dessa matrícula,
    --    adicionando o campo "vinculo" (booleano)
    SELECT json_agg(
               to_jsonb(a) ||
               jsonb_build_object(
                   'vinculo',
                   EXISTS (
                       SELECT 1
                       FROM rel_ass_esc rae
                       WHERE rae.escopo_id = p_escopo_id
                         AND rae.associado_id = a.id
                   )
               )
               ORDER BY a.id
           )
    INTO v_json
    FROM rel_mat_asso r
    JOIN associado a ON a.id = r.associado_id
    WHERE r.matricula = v_matricula;

    RETURN json_build_object(
        'matricula', v_matricula,
        'associados', v_json
    );
END;
$function$