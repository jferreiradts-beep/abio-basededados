CREATE OR REPLACE FUNCTION public.produtos_por_escopo(p_abreviatura text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_tipo_id INTEGER;
BEGIN
    -- 1. Obter o ID do tipo de escopo pela abreviatura
    SELECT id INTO v_tipo_id
    FROM tipo_escopo
    WHERE abreviatura = p_abreviatura;

    IF v_tipo_id IS NULL THEN
        RETURN '{}'::jsonb; -- abreviatura inexistente
    END IF;

    -- 2. Montar o JSON agrupado por grupo
    RETURN (
        SELECT jsonb_object_agg(
            g.nome,
            (
                SELECT jsonb_agg(p.nome ORDER BY p.nome)
                FROM produtos p
                WHERE p.grupo_id = g.id
            )
        )
        FROM grupo_prod g
        WHERE g.tipo_escopo_id = v_tipo_id
    );
END;
$function$
