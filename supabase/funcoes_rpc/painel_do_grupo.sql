CREATE OR REPLACE FUNCTION public.painel_do_grupo(p_grupo_id integer)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
declare
    v_dados_gerais jsonb;
    v_detalhe jsonb;
begin
    --------------------------------------------------------------------
    -- 1) Dados gerais do grupo (com nomes resolvidos)
    --------------------------------------------------------------------
    select jsonb_build_object(
        'id', g.id,
        'nome', g.nome,
        'coordenador', ac.nome
    )
    into v_dados_gerais
    from grupo g
    left join associado ac on ac.id = g.coordenador
    where g.id = p_grupo_id;

    --------------------------------------------------------------------
    -- 2) Detalhe (lista de matrículas + escopos + validade + movimento)
    --------------------------------------------------------------------
    select jsonb_agg(
        jsonb_build_object(
            'id_matricula', m.id,
            'matricula', m.nome,

            'primeiro_associado',
            (
                select a.nome
                from rel_mat_asso r
                join associado a on a.id = r.associado_id
                where r.matricula_id = m.id
                order by a.id
                limit 1
            ),

            'uprod', u.nome,
            'id_escopo', e.id,

            'escopo',
            te.abreviatura ||
            coalesce(
                nullif('-' || trim(both from e.complemento), '-'),
                ''
            ),

            'validade',
            (
                select (a.data + ((e.val_duracao || ' months')::interval) - interval '1 day')::date
                from acontecimentos a
                where a.escopo_id = e.id
                  and a.tipo_id = 1
                order by a.data desc
                limit 1
            ),

            'ultimo_movimento',
            (
                select ta.nome
                from acontecimentos ac
                join tipo_acontecimento ta on ta.id = ac.tipo_id
                where ac.escopo_id = e.id
                  and ac.data <= current_date
                order by ac.data desc, ac.id desc
                limit 1
            )
        )
    )
    into v_detalhe
    from grupo g
    join matricula m on m.grupo_id = g.id
    left join uprod u on u.matricula_id = m.id
    left join escopo e on e.uprod_id = u.id
    left join tipo_escopo te on te.id = e.nome
    where g.id = p_grupo_id;

    --------------------------------------------------------------------
    -- 3) Retorno final como dicionário
    --------------------------------------------------------------------
    return jsonb_build_object(
        'dados_gerais', v_dados_gerais,
        'detalhe', coalesce(v_detalhe, '[]'::jsonb)
    );
end;
$function$
