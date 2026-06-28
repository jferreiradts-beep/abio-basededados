CREATE OR REPLACE FUNCTION public.obter_info_escopo(p_escopo_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_validade DATE;
    v_ultima_atualizacao TEXT;
BEGIN
    -- Última emissão de certificado (tipo_id = 1)
    SELECT (a.data + INTERVAL '1 year' - INTERVAL '1 day')::date
    INTO v_validade
    FROM acontecimentos a
    WHERE a.escopo_id = p_escopo_id
      AND a.tipo_id = 1
    ORDER BY a.data DESC
    LIMIT 1;

    -- Último acontecimento (qualquer tipo)
    SELECT ta.nome
    INTO v_ultima_atualizacao
    FROM acontecimentos a
    JOIN tipo_acontecimento ta ON ta.id = a.tipo_id
    WHERE a.escopo_id = p_escopo_id AND ta.destaque = TRUE
    ORDER BY a.data DESC
    LIMIT 1;

    RETURN json_build_object(
        'validade', v_validade,
        'ultima_atualizacao', v_ultima_atualizacao
    );
END;
$function$