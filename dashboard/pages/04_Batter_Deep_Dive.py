import streamlit as st,pandas as pd,numpy as np,plotly.express as px,plotly.graph_objects as go
from utils import *
f=st.session_state['global_filters']; allp=player_tables('Batter'); p=filtered(allp,f)
st.title('Batter Deep-Dive')
if p.empty: empty()
else:
    ids=p.sort_values('model_b_rank').player_id.tolist(); finals=load_csv('final_top10.csv'); fn=finals[finals.role.eq('Batter')]
    default=int(fn.sort_values('rank').iloc[0].player_id)
    stored=st.session_state.get('selected_batter_id')
    if stored not in set(allp.player_id): stored=default
    if stored not in ids: ids=[stored]+ids
    ids=[stored]+[i for i in ids if i!=stored]
    choices=dict(zip(allp.player_id,allp.name)); choice_key='batter_player_choice'
    if st.session_state.get(choice_key) not in ids: st.session_state[choice_key]=stored
    one=st.selectbox('Player',ids,index=0,format_func=lambda z:choices.get(z,str(z)),key=choice_key)
    st.session_state['selected_batter_id']=int(one)
    compare=st.toggle('Compare two batters'); two=st.selectbox('Compare with',ids,format_func=lambda z:choices.get(z,str(z)),index=1 if len(ids)>1 else 0) if compare else None
    row=p[p.player_id.eq(one)].iloc[0]
    st.subheader(row['name']); st.caption(f"Teams: {team_display(row)} · Model B rank {int(row.model_b_rank)}")
    st.caption('Saved player rating metrics reflect the full analysis period; delivery-level views below follow the active competition and season filters.')
    if bool(row.get('rank_uncertain',False)): st.warning('Model A rank is flagged as uncertain by the bootstrap reliability check.')
    ci=f"[{display_number(row.get('rating_ci_low'))}, {display_number(row.get('rating_ci_high'))}]"
    cols=st.columns(5)
    for c,(label,val) in zip(cols,[('Model B score',display_number(row.get('model_b_score'))),('Model A rating',f"{display_number(row.get('model_a_rating'))} {ci}"),('Top-10 inclusion',display_number(row.get('bootstrap_top10_pct'),1,'%')),('Pressure balls',display_number(row.get('pressure_balls'),0)),('Clutch delta',display_number(row.get('clutch_delta'),3,' RAE/ball'))]):
        with c: metric_card(label, f'{val:.2f}' if isinstance(val,(float,int)) and label=='Rating' else str(val))
    metrics=[('Strike rate',row.get('pressure_strike_rate'),row.get('baseline_strike_rate'),'runs / 100 balls',1),
             ('Dot-ball rate',row.get('pressure_dot_pct'),row.get('baseline_dot_pct'),'% of balls',100),
             ('Boundary rate',row.get('pressure_boundary_pct'),row.get('baseline_boundary_pct'),'% of balls',100),
             ('Dismissals',100/row.pressure_balls_per_dismissal if pd.notna(row.get('pressure_balls_per_dismissal')) and row.pressure_balls_per_dismissal else np.nan,
              100/row.baseline_balls_per_dismissal if pd.notna(row.get('baseline_balls_per_dismissal')) and row.baseline_balls_per_dismissal else np.nan,'dismissals / 100 balls',1)]
    st.plotly_chart(metric_comparison_grid(metrics,'Batting performance: pressure vs baseline'),use_container_width=True)
    if compare and two!=one:
        pair=p[p.player_id.isin([one,two])]; cv=[]
        for _,pr in pair.iterrows():
            for label,col in [('Pressure','pressure_strike_rate'),('Baseline','baseline_strike_rate')]: cv.append({'Player':pr['name'],'State':label,'Strike rate':pr.get(col)})
        st.plotly_chart(plot_theme(px.bar(pd.DataFrame(cv),x='Player',y='Strike rate',color='State',barmode='group',color_discrete_map={'Pressure':PINK,'Baseline':BLUE},title='Head-to-head strike rate')),use_container_width=True)
    pm=load_csv('player_match_pressure.csv'); pm=pm[(pm.role=='Batter')&(pm.player_id==one)]; pm=filtered(pm,f)
    if not pm.empty:
        pm=pm.sort_values(['match_date','match_id']); pm['match_label']=pd.to_datetime(pm.match_date,errors='coerce').dt.strftime('%Y-%m-%d')+' · '+pm.match_id.astype(str)
        y='RAE'; pm[y]=pd.to_numeric(pm.get('RAE'),errors='coerce')
        st.plotly_chart(plot_theme(px.bar(pm,x='match_label',y=y,color=y,color_continuous_scale=[RED,'#dfe7f2',GREEN],hover_data={'pressure_impact_per_ball':':.3f'},title='Runs above expected by match under pressure',labels={'match_label':'Match date · ID',y:'Runs above expected (runs)','pressure_impact_per_ball':'Impact per ball (runs/ball)'})),use_container_width=True)
    tabs=st.tabs(['Splits available','Eligible-player comparison'])
    with tabs[0]:
        splitcols=[c for c in ['phase','innings','batting_order','pace_or_spin','competition'] if c in deliveries().columns]
        d=filtered(deliveries(),f); d=d[(d.striker_id==one)&pressure_mask(d,'bat',f)]
        found_comp=False
        for dim in splitcols:
            if d[dim].notna().any():
                if dim=='competition': found_comp=True
                agg=d.groupby(dim,dropna=False).agg(balls=('legal_ball','sum'),rae=('batter_rae','mean')).reset_index()
                st.plotly_chart(plot_theme(px.bar(agg,x=dim,y='rae',title=f'Pressure impact by {dim}',labels={'rae':'RAE per delivery'})),use_container_width=True)
        if not found_comp: st.caption('Competition splits: n/a for the current player and filters.')
    with tabs[1]:
        elig=p[p.pressure_balls.ge(f['min_bat'])].copy(); d=elig; final_ids=set(fn.player_id)
        if d.empty: empty('No batters meet the current pressure-ball threshold.')
        else:
            fig=px.scatter(d,x='baseline_strike_rate',y='pressure_strike_rate',color=d.player_id.isin(final_ids).map({True:'Final list',False:'Other eligible'}),hover_name='name',hover_data=['pressure_balls','model_b_rank'],color_discrete_map={'Final list':PINK,'Other eligible':BLUE},title='Eligible batters · baseline vs pressure strike rate',labels={'baseline_strike_rate':'Baseline strike rate (runs/100 balls)','pressure_strike_rate':'Pressure strike rate (runs/100 balls)'})
            maxv=max(pd.to_numeric(d.baseline_strike_rate,errors='coerce').max(),pd.to_numeric(d.pressure_strike_rate,errors='coerce').max()); fig.add_shape(type='line',x0=0,y0=0,x1=maxv,y1=maxv,line=dict(color='#7b879d',dash='dash'))
            st.plotly_chart(plot_theme(fig),use_container_width=True)
footer()
