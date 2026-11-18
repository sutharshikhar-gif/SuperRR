import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils import *

f=st.session_state['global_filters']
full=deliveries()
d=filtered(full,f)
st.title('Match Explorer')
if full.empty:
    empty('Delivery-level match data is unavailable.')
else:
    meta_cols=['match_id','match_date','batting_team','bowling_team','competition','season','season_year']
    match_meta=full[meta_cols].drop_duplicates('match_id').copy()
    match_meta['date']=pd.to_datetime(match_meta.match_date,errors='coerce')
    match_meta['label']=match_meta.date.dt.strftime('%Y-%m-%d').fillna(match_meta.match_date.astype(str))+' · '+match_meta.batting_team.astype(str)+' vs '+match_meta.bowling_team.astype(str)+' · '+match_meta.match_id.astype(str)

    preset1=match_meta[match_meta.date.dt.strftime('%Y-%m-%d').eq('2025-04-10') & (match_meta.batting_team.astype(str).str.contains('Delhi',case=False,na=False)|match_meta.bowling_team.astype(str).str.contains('Delhi',case=False,na=False)) & (match_meta.batting_team.astype(str).str.contains('Bangalore|Bengaluru|Royal Challengers|RCB',case=False,na=False)|match_meta.bowling_team.astype(str).str.contains('Bangalore|Bengaluru|Royal Challengers|RCB',case=False,na=False))]
    preset2=match_meta[match_meta.date.dt.strftime('%Y-%m-%d').eq('2023-05-29') & match_meta.batting_team.astype(str).str.contains('Gujarat',case=False,na=False) & match_meta.bowling_team.astype(str).str.contains('Chennai',case=False,na=False)]
    q1,q2=st.columns(2)
    with q1:
        if st.button('Delhi Capitals chase vs RCB · 10 Apr 2025',use_container_width=True):
            if not preset1.empty:
                st.session_state['match_choice']=int(preset1.iloc[0].match_id)
                st.session_state['match_selector']=preset1.iloc[0].label
                st.session_state['match_innings_choice']=2
                st.session_state['innings_selector']=2
                st.session_state['match_pressure_role']='Batting'
            else: st.warning('The Delhi Capitals vs RCB example is not present in the prepared delivery data.')
    with q2:
        if st.button('GT vs CSK · 29 May 2023',use_container_width=True):
            if not preset2.empty:
                st.session_state['match_choice']=int(preset2.iloc[0].match_id)
                st.session_state['match_selector']=preset2.iloc[0].label
                st.session_state['match_innings_choice']=1
                st.session_state['innings_selector']=1
                st.session_state['match_pressure_role']='Bowling'
            else: st.warning('The GT vs CSK example is not present in the prepared delivery data.')

    st.radio('Pressure view',['Batting','Bowling'],horizontal=True,key='match_pressure_role',index=0 if st.session_state.get('match_pressure_role','Batting')=='Batting' else 1)
    options=match_meta.copy()
    if f['competition']!='Both': options=options[options.competition.astype(str).eq(f['competition'])]
    options=options[pd.to_numeric(options.season_year,errors='coerce').between(*f['years'])]
    comps=st.multiselect('Competition',sorted(options.competition.dropna().astype(str).unique()),default=sorted(options.competition.dropna().astype(str).unique()),key='match_comp_filter')
    seasons=st.multiselect('Season',sorted(options.season.dropna().astype(str).unique()),default=sorted(options.season.dropna().astype(str).unique()),key='match_season_filter')
    dates=options.date.dropna()
    if not dates.empty:
        date_range=st.date_input('Match date range',(dates.min().date(),dates.max().date()),key='match_date_filter')
        if isinstance(date_range,tuple) and len(date_range)==2:
            options=options[options.date.dt.date.between(date_range[0],date_range[1])]
    options=options[options.competition.astype(str).isin(comps)&options.season.astype(str).isin(seasons)]
    team_values=sorted(set(options.batting_team.dropna().astype(str))|set(options.bowling_team.dropna().astype(str)))
    team=st.selectbox('Team (either side)',['All']+team_values,key='match_team_filter')
    if team!='All': options=options[options.batting_team.astype(str).eq(team)|options.bowling_team.astype(str).eq(team)]

    selected=st.session_state.get('match_choice')
    # Keep preset examples open even when global/sidebar filters would otherwise hide them.
    if selected is not None and not options.match_id.eq(int(selected)).any():
        preset=match_meta[match_meta.match_id.eq(int(selected))]
        if not preset.empty:
            options=pd.concat([options,preset],ignore_index=True).drop_duplicates('match_id')
            st.info('The selected example is outside the current match filters, so it is shown anyway. Adjust filters to return to the filtered list.')
    options=options.sort_values(['date','match_id'])
    labels=options.label.tolist()
    if not labels:
        empty('No matches match these filters.')
    else:
        default_label=next((r.label for _,r in options.iterrows() if selected is not None and int(r.match_id)==int(selected)),labels[0])
        if st.session_state.get('match_selector') not in labels: st.session_state['match_selector']=default_label
        chosen=st.selectbox('Match',labels,key='match_selector')
        mid=int(options.loc[options.label.eq(chosen),'match_id'].iloc[0])
        st.session_state['match_choice']=mid
        md=full[full.match_id.eq(mid)]
        inning_options=sorted(pd.to_numeric(md.innings,errors='coerce').dropna().astype(int).unique())
        preferred=st.session_state.get('match_innings_choice',inning_options[0] if inning_options else None)
        if preferred not in inning_options: preferred=inning_options[0]
        inning_labels={1:'1 · First innings',2:'2 · Chase',3:'3 · Super over',4:'4 · Super over'}
        inn=st.selectbox('Innings',inning_options,index=inning_options.index(preferred),format_func=lambda n:inning_labels.get(n,str(n)),key='innings_selector')
        x=md[pd.to_numeric(md.innings,errors='coerce').eq(inn)].sort_values('innings_ball_num').copy()
        if x.empty: empty('No delivery rows for this innings.')
        else:
            st.caption(f"{x.competition.iloc[0]} · {x.season.iloc[0]} · {x.batting_team.iloc[0]} batting")
            bat_flag=x.bat_pressure_flag.fillna(False).astype(bool)
            bowl_flag=x.bowl_pressure_flag.fillna(False).astype(bool)
            active_flag=bat_flag if st.session_state['match_pressure_role']=='Batting' else bowl_flag
            chartflag=active_flag & x.legal_ball.fillna(False).astype(bool)
            metric='rrr_crr_gap' if inn==2 else 'par_gap'
            metric_label='RRR − CRR gap (runs/over)' if inn==2 else 'Par minus score (runs)'
            if metric in x and x[metric].notna().any():
                fig=px.line(x,x='innings_ball_num',y=metric,title=f'Ball-by-ball state · {metric_label}',labels={'innings_ball_num':'Delivery number','rrr_crr_gap':metric_label,'par_gap':metric_label})
                wickets=x[x.is_wicket.fillna(False).astype(bool)]
                fig.add_scatter(x=wickets.innings_ball_num,y=wickets[metric],mode='markers+text',text=['+1w']*len(wickets),textposition='top center',name='Wicket',marker=dict(color=NAVY,symbol='x',size=10))
                flagged=x[chartflag]
                fig.add_scatter(x=flagged.innings_ball_num,y=flagged[metric],mode='markers',name=f"{st.session_state['match_pressure_role']} pressure",marker=dict(color=PINK,size=8,opacity=.9))
                st.plotly_chart(plot_theme(fig),use_container_width=True)
            x['team_runs']=pd.to_numeric(x.total_runs,errors='coerce').fillna(0)
            x['bowling_flag']=bowl_flag
            ov=x.groupby('overid',as_index=False).agg(runs=('team_runs','sum'),bowling_pressure=('bowling_flag','max'),wickets=('is_wicket','sum'))
            ov['wicket_label']=np.where(ov.wickets.gt(0),ov.wickets.map(lambda n:f'+{int(n)}w'),'')
            fig=px.bar(ov,x='overid',y='runs',color='bowling_pressure',text='wicket_label',color_discrete_map={True:PINK,False:BLUE},title='Over-by-over team runs · pink marks bowling-pressure overs',labels={'overid':'Over','runs':'Team runs','bowling_pressure':'Bowling-pressure over','wicket_label':'Wickets'})
            fig.update_traces(textposition='outside',cliponaxis=False)
            st.plotly_chart(plot_theme(fig),use_container_width=True)

            st.subheader('Batters and bowlers involved')
            legal=x[x.legal_ball.fillna(False).astype(bool)].copy()
            legal['bat_flag']=legal.bat_pressure_flag.fillna(False).astype(bool)
            legal['bowl_flag']=legal.bowl_pressure_flag.fillna(False).astype(bool)
            bat=legal.groupby(['striker_id','striker_name'],dropna=False).agg(pressure_balls=('bat_flag','sum'),pressure_runs=('runs',lambda s:s[legal.loc[s.index,'bat_flag']].sum()),legal_balls=('legal_ball','sum')).reset_index()
            bowl=legal.groupby(['bowler_id','bowler_name'],dropna=False).agg(pressure_balls=('bowl_flag','sum'),runs_conceded=('bowler_runs_conceded',lambda s:s[legal.loc[s.index,'bowl_flag']].sum()),legal_balls=('legal_ball','sum')).reset_index()
            c1,c2=st.columns(2)
            with c1: st.dataframe(bat.rename(columns={'striker_name':'Batter','pressure_runs':'Batting-pressure runs'}),hide_index=True,use_container_width=True)
            with c2: st.dataframe(bowl.rename(columns={'bowler_name':'Bowler','runs_conceded':'Bowling-pressure runs conceded'}),hide_index=True,use_container_width=True)
footer()
