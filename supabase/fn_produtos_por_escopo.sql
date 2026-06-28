CREATE OR REPLACE FUNCTION public.fn_produtos_por_escopo(p_tipo integer, p_escopo_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_produtos_escopo INT[];
BEGIN
    -- carrega todos os produtos do escopo em um array
    SELECT array_agg(produto_id)
    INTO v_produtos_escopo
    FROM rel_esc_prod
    WHERE escopo_id = p_escopo_id;

    RETURN (
        SELECT json_build_object(
            'escopo', (
                SELECT json_build_object(
                    'nucleo', mv.nucleo,
                    'grupo', mv.grupo,
                    'matricula', mv.matricula,
                    'primeiro_associado', mv.primeiro_associado
                )
                FROM vw_dados_com_associado mv
                WHERE mv.id_escopo = p_escopo_id
            ),
            'grupos', (
                SELECT json_agg(
                    json_build_object(
                        'id', g.id,
                        'nome', g.nome,
                        'produtos', COALESCE(
                            (
                                SELECT json_agg(
                                    json_build_object(
                                        'id', p.id,
                                        'nome', p.nome,
                                        'incluso', p.id = ANY(v_produtos_escopo)
                                    )
                                )
                                FROM produtos p
                                WHERE p.grupo_id = g.id
                            ),
                            '[]'::json
                        )
                    )
                )
                FROM grupo_prod g
                JOIN tipo_escopo te ON te.id = g.tipo_escopo_id
                WHERE te.id = p_tipo
            )
        )
    );
END;
$function$