CREATE OR REPLACE FUNCTION public.dados_de_matricula(matricula_input text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN jsonb_build_object(
        'dados gerais',
            (
                SELECT jsonb_build_object(
                    'matricula', m.matricula,
                    'grupo', m.grupo_id
                )
                FROM matriculas m
                WHERE m.matricula = matricula_input
            ),

        -- grupos permanece como estava
        'grupos',
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'id', g.id,
                        'nome', g.nome
                    )
                )
                FROM grupo g
            ),

        -- associados → lista vazia se não houver
        'associados',
            COALESCE(
                (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'id', a.id,
                            'cpf', a.cpf,
                            'nome', a.nome
                        )
                    )
                    FROM associado a
                    JOIN rel_mat_asso r
                        ON r.associado_id = a.id
                    WHERE r.matricula = matricula_input
                ),
                '[]'::jsonb
            ),

        -- escopos → lista vazia se não houver
        'escopos',
            COALESCE(
                (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'id', e.id,
                            'nome', RTRIM(te.abreviatura || '-' || COALESCE(NULLIF(e.complemento, ''), ''), '-')
                        )
                    )
                    FROM escopo e
                    JOIN tipo_escopo te
                      ON te.id = e.nome
                    WHERE e.matricula = matricula_input
                ),
                '[]'::jsonb
            ),

        -- uprods → lista vazia se não houver
        'uprods',
            COALESCE(
                (
                    SELECT jsonb_agg(DISTINCT
                        jsonb_build_object(
                            'id', u.id,
                            'nome', u.nome
                        )
                    )
                    FROM uprod u
                    JOIN escopo e 
                      ON u.id = e.uprod_id
                    WHERE e.matricula = matricula_input
                ),
                '[]'::jsonb
            )
    );
END;
$function$