import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

f=st.session_state['global_filters']
final=load_csv('final_top10.csv')
comparison=load_csv('model_comparison.csv')
published=load_csv('model_c_published_ranks.csv')
st.title('Final Top 10 and Evidence')
st.caption('The submitted Model B lists remain in their fixed order. Comparison ranks are shown as published in methodology report v3.')

for role in ['Batter','Bowler']:
    st.subheader(f'{role}s')
    q=final[final.role.eq(role)].merge(comparison,on=['role','player_id','name'],how='left',suffixes=('','_comparison'))
    q['Model A']=q.model_a_rank.map(lambda v:f'#{int(v)}' if pd.notna(v) and v<=10 else 'Outside top 10')
    def c_label(row):
        rank=row.model_c_rank
        if pd.isna(rank): return 'below minimum' if row.get('model_c_status')=='below minimum' else 'n/a'
        return f'#{int(rank)} of {int(row.get("model_c_pool_size",160 if role=="Batter" else 155))}'
    q['Model C published v3']=q.apply(c_label,axis=1)
    q['Model C rank']=pd.to_numeric(q.model_c_rank,errors='coerce')
    st.dataframe(q[['rank','name','Model A','Model C published v3']].rename(columns={'rank':'Final rank','name':'Player'}),hide_index=True,use_container_width=True)

    points=[]
    for _,r in q.iterrows():
        points.append({'Player':r['name'],'Model':'Final list','Status':'Final Model B list','Rank':int(r['rank'])})
        a_rank=pd.to_numeric(pd.Series([r.model_a_rank]),errors='coerce').iloc[0]
        points.append({'Player':r['name'],'Model':'Model A','Status':'Top 10' if pd.notna(a_rank) and a_rank<=10 else 'Outside top 10','Rank':a_rank if pd.notna(a_rank) else None})
        c_rank=pd.to_numeric(pd.Series([r.model_c_rank]),errors='coerce').iloc[0]
        if pd.isna(c_rank): c_status='Below minimum' if r.get('model_c_status')=='below minimum' else 'Not published'
        elif c_rank<=10: c_status='Top 10'
        elif c_rank<=20: c_status='Ranks 11–20'
        else: c_status='Outside top 20'
        points.append({'Player':r['name'],'Model':'Model C published v3','Status':c_status,'Rank':c_rank if pd.notna(c_rank) else None})
    points=pd.DataFrame(points)
    colors={'Final Model B list':NAVY,'Top 10':PINK,'Outside top 10':PINK,'Ranks 11–20':'#91cf9b','Outside top 20':'#538d5c','Below minimum':'#aab3c2','Not published':'#aab3c2'}
    symbols={'Final Model B list':'circle','Top 10':'circle','Outside top 10':'circle-open','Ranks 11–20':'circle','Outside top 20':'circle-open','Below minimum':'x','Not published':'x'}
    fig=px.scatter(points,x='Model',y='Player',color='Status',symbol='Status',hover_data=['Rank'],title=f'{role}: final list agreement with Model A and Model C',color_discrete_map=colors,symbol_map=symbols)
    fig.update_traces(marker_size=12,marker_line_width=2)
    fig.update_layout(yaxis={'categoryorder':'array','categoryarray':q.name.tolist()[::-1]},xaxis_title='Model',yaxis_title='',legend_title='Rank position')
    st.plotly_chart(plot_theme(fig,430),use_container_width=True)

    players=player_tables(role)
    evidence=final[final.role.eq(role)].merge(players,on=['player_id','name'],how='left')
    for _,r in evidence.sort_values('rank').iterrows():
        with st.expander(f"#{int(r['rank'])} · {r['name']}"):
            metric='pressure_strike_rate' if role=='Batter' else 'pressure_economy'
            base='baseline_strike_rate' if role=='Batter' else 'baseline_economy'
            unit='runs/100 balls' if role=='Batter' else 'runs/over'
            if pd.notna(r.get(metric)) and pd.notna(r.get(base)):
                st.write(f"Pressure {metric.replace('pressure_','').replace('_',' ')}: {r[metric]:.2f} {unit}; baseline: {r[base]:.2f} {unit}; pressure sample: {int(r.get('pressure_balls',0))} balls.")
            else: st.write('Evidence metric: n/a in the supplied files.')
            st.caption(f"Model B score: {display_number(r.get('model_b_score'))} · Model A rank: {int(r.model_a_rank) if pd.notna(r.get('model_a_rank')) else 'Outside top 10'} · Model C published v3 rank: {c_label(r)}")
footer()
