import streamlit as st,pandas as pd,plotly.express as px,plotly.graph_objects as go
from utils import *
f=st.session_state['global_filters']; allp=player_tables('Bowler'); p=filtered(allp,f)
st.title('Bowler Deep-Dive')
if p.empty: empty()
else:
    finals=load_csv('final_top10.csv'); fn=finals[finals.role.eq('Bowler')]; ids=p.sort_values('model_b_rank').player_id.tolist()
    default=int(fn.sort_values('rank').iloc[0].player_id)
    stored=st.session_state.get('selected_bowler_id')
    if stored not in set(allp.player_id): stored=default
    if stored not in ids: ids=[stored]+ids
    ids=[stored]+[i for i in ids if i!=stored]
    choices=dict(zip(allp.player_id,allp.name)); choice_key='bowler_player_choice'
    if st.session_state.get(choice_key) not in ids: st.session_state[choice_key]=stored
    one=st.selectbox('Player',ids,index=0,format_func=lambda z:choices.get(z,str(z)),key=choice_key)
    st.session_state['selected_bowler_id']=int(one)
    compare=st.toggle('Compare two bowlers'); two=st.selectbox('Compare with',ids,format_func=lambda z:choices.get(z,str(z)),index=1 if len(ids)>1 else 0) if compare else None
    row=p[p.player_id.eq(one)].iloc[0]; st.subheader(row['name']); st.caption(f"Teams: {team_display(row)} · Model B rank {int(row.model_b_rank)}")
    st.caption('Saved player rating metrics reflect the full analysis period; delivery-level views below follow the active competition and season filters.')
    if bool(row.get('rank_uncertain',False)): st.warning('Model A rank is flagged as uncertain by the bootstrap reliability check.')
    ci=f"[{display_number(row.get('rating_ci_low'))}, {display_number(row.get('rating_ci_high'))}]"
    cols=st.columns(5)
    for c,(label,val) in zip(cols,[('Model B score',display_number(row.get('model_b_score'))),('Model A rating',f"{display_number(row.get('model_a_rating'))} {ci}"),('Top-10 inclusion',display_number(row.get('bootstrap_top10_pct'),1,'%')),('Pressure balls',display_number(row.get('pressure_balls'),0)),('Clutch delta',display_number(row.get('clutch_delta'),3,' runs saved/ball'))]):
        with c: metric_card(label, f'{val:.2f}' if isinstance(val,(float,int)) and label=='Rating' else str(val))
    pres=['pressure_economy','pressure_dot_pct','pressure_boundary_pct','pressure_wickets_per_ball']; base=['baseline_economy','baseline_dot_pct','baseline_boundary_pct','baseline_wickets_per_ball']
    names=['Economy (runs/over)','Dot balls (%)','Boundary conceded (%)','Wickets per ball']
    metrics=[('Economy',row.get('pressure_economy'),row.get('baseline_economy'),'runs / over',1),
             ('Dot-ball rate',row.get('pressure_dot_pct'),row.get('baseline_dot_pct'),'% of legal balls',100),
             ('Boundary conceded',row.get('pressure_boundary_pct'),row.get('baseline_boundary_pct'),'% of legal balls',100),
             ('Wickets',row.get('pressure_wickets_per_ball'),row.get('baseline_wickets_per_ball'),'wickets / 100 legal balls',100)]
    st.plotly_chart(metric_comparison_grid(metrics,'Bowling performance: pressure vs baseline'),use_container_width=True)
    if compare and two!=one:
        pair=p[p.player_id.isin([one,two])]; cv=[]
        for _,pr in pair.iterrows():
            for label,col in [('Pressure','pressure_economy'),('Baseline','baseline_economy')]: cv.append({'Player':pr['name'],'State':label,'Economy':pr.get(col)})
        st.plotly_chart(plot_theme(px.bar(pd.DataFrame(cv),x='Player',y='Economy',color='State',barmode='group',color_discrete_map={'Pressure':PINK,'Baseline':BLUE},title='Head-to-head economy')),use_container_width=True)
    st.markdown('<div class="note">A bowler can rank well with a higher pressure economy because expected economy in these situations is already about 11.7 runs per over.</div>',unsafe_allow_html=True)
    pm=load_csv('player_match_pressure.csv'); pm=pm[(pm.role=='Bowler')&(pm.player_id==one)]; pm=filtered(pm,f)
    if not pm.empty:
        pm=pm.sort_values(['match_date','match_id']); pm['match_label']=pd.to_datetime(pm.match_date,errors='coerce').dt.strftime('%Y-%m-%d')+' · '+pm.match_id.astype(str)
        y='runs_saved_above_expected'
        st.plotly_chart(plot_theme(px.bar(pm,x='match_label',y=y,color=y,color_continuous_scale=[RED,'#dfe7f2',GREEN],hover_data={'pressure_impact_per_ball':':.3f'},title='Runs saved above expected by match under pressure',labels={'match_label':'Match date · ID',y:'Runs saved above expected (runs)','pressure_impact_per_ball':'Impact per ball (runs/ball)'})),use_container_width=True)
    tabs=st.tabs(['Death overs and bowling type','Eligible-player comparison'])
    with tabs[0]:
        d=filtered(deliveries(),f); d=d[(d.bowler_id==one)&d.bowl_pressure_flag.fillna(False)]
        death=d[d.overid.between(15,20)].groupby('overid',as_index=False).agg(runs=('bowler_runs_conceded','sum'),balls=('legal_ball','sum')); death['economy']=death.runs*6/death.balls.replace(0,np.nan)
        if not death.empty: st.plotly_chart(plot_theme(px.bar(death,x='overid',y='economy',title='Death-over economy by over',labels={'overid':'Over','economy':'Economy (runs/over)'})),use_container_width=True)
        found_comp=False
        for dim in ['phase','pace_or_spin','competition']:
            if dim in d and d[dim].notna().any():
                if dim=='competition': found_comp=True
                ag=d.groupby(dim).agg(runs=('bowler_runs_conceded','sum'),balls=('legal_ball','sum')).reset_index(); ag['economy']=ag.runs*6/ag.balls.replace(0,np.nan)
                st.plotly_chart(plot_theme(px.bar(ag,x=dim,y='economy',title=f'Pressure economy by {dim}',labels={'economy':'Economy (runs/over)'})),use_container_width=True)
        if not found_comp: st.caption('Competition splits: n/a for the current player and filters.')
    with tabs[1]:
        final_ids=set(fn.player_id); elig=p[p.pressure_balls.ge(f['min_bowl'])].copy()
        if elig.empty: empty('No bowlers meet the current pressure-ball threshold.')
        else:
            fig=px.scatter(elig,x='baseline_economy',y='pressure_economy',color=elig.player_id.isin(final_ids).map({True:'Final list',False:'Other eligible'}),hover_name='name',hover_data=['pressure_balls','model_b_rank'],color_discrete_map={'Final list':PINK,'Other eligible':BLUE},title='Eligible bowlers · baseline vs pressure economy',labels={'baseline_economy':'Baseline economy (runs/over)','pressure_economy':'Pressure economy (runs/over)'})
            maxv=max(pd.to_numeric(elig.baseline_economy,errors='coerce').max(),pd.to_numeric(elig.pressure_economy,errors='coerce').max()); fig.add_shape(type='line',x0=0,y0=0,x1=maxv,y1=maxv,line=dict(color='#7b879d',dash='dash'))
            st.plotly_chart(plot_theme(fig),use_container_width=True)
footer()
