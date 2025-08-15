--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Postgres.app)
-- Dumped by pg_dump version 17.5 (Postgres.app)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: feedback_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.feedback_enum AS ENUM (
    'like',
    'neutral',
    'dislike'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: circle_memberships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.circle_memberships (
    id integer NOT NULL,
    user_id integer NOT NULL,
    circle_id integer NOT NULL,
    joined_at timestamp without time zone NOT NULL
);


--
-- Name: circle_membership_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.circle_membership_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: circle_membership_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.circle_membership_id_seq OWNED BY public.circle_memberships.id;


--
-- Name: song_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.song_feedback (
    id integer NOT NULL,
    user_id integer NOT NULL,
    song_id integer NOT NULL,
    feedback character varying(10) NOT NULL,
    "timestamp" timestamp without time zone
);


--
-- Name: song_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.song_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: song_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.song_feedback_id_seq OWNED BY public.song_feedback.id;


--
-- Name: sound_circles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sound_circles (
    id integer NOT NULL,
    circle_name character varying(100) NOT NULL,
    drop_frequency character varying(20) NOT NULL,
    drop_day1 character varying(20),
    drop_day2 character varying(20),
    drop_time timestamp without time zone NOT NULL,
    invite_code character varying(10),
    creator_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: sound_circle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sound_circle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sound_circle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sound_circle_id_seq OWNED BY public.sound_circles.id;


--
-- Name: submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    circle_id integer NOT NULL,
    user_id integer NOT NULL,
    spotify_track_id character varying(100) NOT NULL,
    cycle_date date NOT NULL,
    submitted_at timestamp with time zone NOT NULL,
    visible_to_others boolean
);


--
-- Name: submission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.submission_id_seq OWNED BY public.submissions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    spotify_id character varying(128) NOT NULL,
    vibedrop_username character varying(64) NOT NULL,
    display_name character varying(128),
    email character varying(128),
    access_token character varying(1024) NOT NULL,
    refresh_token character varying(1024),
    expires_at timestamp without time zone,
    drop_cred double precision,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public.users.id;


--
-- Name: vibe_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vibe_scores (
    id integer NOT NULL,
    user1_id integer NOT NULL,
    user2_id integer NOT NULL,
    vibe_index double precision NOT NULL,
    last_updated timestamp without time zone NOT NULL
);


--
-- Name: vibe_score_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vibe_score_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vibe_score_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vibe_score_id_seq OWNED BY public.vibe_scores.id;


--
-- Name: circle_memberships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.circle_memberships ALTER COLUMN id SET DEFAULT nextval('public.circle_membership_id_seq'::regclass);


--
-- Name: song_feedback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback ALTER COLUMN id SET DEFAULT nextval('public.song_feedback_id_seq'::regclass);


--
-- Name: sound_circles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sound_circles ALTER COLUMN id SET DEFAULT nextval('public.sound_circle_id_seq'::regclass);


--
-- Name: submissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submissions ALTER COLUMN id SET DEFAULT nextval('public.submission_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: vibe_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vibe_scores ALTER COLUMN id SET DEFAULT nextval('public.vibe_score_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
10e45ad2b0d2
\.


--
-- Data for Name: circle_memberships; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.circle_memberships (id, user_id, circle_id, joined_at) FROM stdin;
1	1	1	2025-08-07 14:49:47.245475
2	1	2	2025-08-07 15:26:35.323571
3	1	3	2025-08-07 15:47:51.044401
4	1	4	2025-08-07 15:48:26.602886
5	1	5	2025-08-08 10:07:15.219839
6	1	6	2025-08-08 20:57:52.337975
7	1	7	2025-08-08 20:59:30.307543
8	1	8	2025-08-10 18:59:53.296348
9	1	9	2025-08-11 15:35:31.755277
\.


--
-- Data for Name: song_feedback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.song_feedback (id, user_id, song_id, feedback, "timestamp") FROM stdin;
1	1	9	like	2025-08-11 20:47:17.970702
\.


--
-- Data for Name: sound_circles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sound_circles (id, circle_name, drop_frequency, drop_day1, drop_day2, drop_time, invite_code, creator_id, created_at) FROM stdin;
1	LOCAL test 1	Daily	Monday	Monday	2025-08-07 15:00:00	ASMDRJWC	1	2025-08-07 14:49:47.232383
2	LOCAL test 2 5pm EST	Daily	Monday	Monday	2025-08-07 16:00:00	b5TSqMMr	1	2025-08-07 15:26:35.317472
3	LOCAL test 3 6pm EST	Daily	Monday	Monday	2025-08-07 17:00:00	Kh3voc7w	1	2025-08-07 15:47:51.031482
4	LOCAL test 4 7pm EST	Daily	Monday	Monday	2025-08-07 18:00:00	4m8z0NER	1	2025-08-07 15:48:26.598587
5	LOCAL biweekly test	Biweekly	Friday	Saturday	2025-08-08 10:00:00	rnYBauJd	1	2025-08-08 10:07:15.207261
6	LOCAL Test Weekly 10pm EST	Weekly	Friday	Monday	2025-08-08 21:00:00	wDeUm05R	1	2025-08-08 20:57:52.328039
7	LOCAL Test Weekly 11pm EST	Weekly	Friday	Monday	2025-08-08 22:00:00	rOf51C3r	1	2025-08-08 20:59:30.301429
8	LOCAL 9PM DIALY	Daily	Monday	Monday	2025-08-10 20:00:00	K4UDlxyi	1	2025-08-10 18:59:53.280287
9	LOCAL Test Weekly 5pm Mondays	Weekly	Monday	Monday	2025-08-11 16:00:00	s45Ch53w	1	2025-08-11 15:35:31.744907
\.


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.submissions (id, circle_id, user_id, spotify_track_id, cycle_date, submitted_at, visible_to_others) FROM stdin;
1	1	1	4Zbsau2HqGebCOrUxQJzEl	2025-08-07	2025-08-07 14:51:08.822823-05	f
2	2	1	3PpxUVqvRIkVV7q5jWiQK9	2025-08-07	2025-08-07 15:26:55.285818-05	f
3	3	1	4YS0MW1khH9F0Ktg4QgMZN	2025-08-07	2025-08-07 15:47:58.203684-05	f
4	4	1	7H3bWxgjLiSnwStlBGgAlG	2025-08-07	2025-08-07 15:48:48.189816-05	f
5	2	1	30l8jqVysaGj7bPcGSVUgD	2025-08-07	2025-08-07 20:58:28.141362-05	f
6	5	1	7H3bWxgjLiSnwStlBGgAlG	2025-08-08	2025-08-08 10:07:39.266722-05	f
7	4	1	6uToph829N0d0VyfouEYer	2025-08-07	2025-08-08 14:50:02.029746-05	f
8	6	1	3PczYtUqSoEXhXQlzbMDIG	2025-08-08	2025-08-08 20:58:48.842896-05	f
9	7	1	4OjV2BCKlDBmUakKOARRqt	2025-08-01	2025-08-08 20:59:46.189679-05	f
10	2	1	1gPeJMO7Az6ZtzHiaKUTWb	2025-08-10	2025-08-10 16:46:43.440035-05	f
11	2	1	0lEWIegMNMQ7W1ooB1zWT2	2025-08-10	2025-08-10 16:54:43.661891-05	f
12	8	1	4zWuKPeehpXHrI5XaicAcf	2025-08-11	2025-08-10 19:00:03.789668-05	f
13	3	1	5zFaNeTwCtsBbMc72FtXVo	2025-08-10	2025-08-11 14:00:09.735532-05	f
14	1	1	6iTAtdjDzH8f3D1KcASfQQ	2025-08-11	2025-08-11 15:34:26.822157-05	f
15	9	1	6iTAtdjDzH8f3D1KcASfQQ	2025-08-11	2025-08-11 15:35:37.860262-05	f
16	7	1	1jx6eeZr6A1SbniFvvUru7	2025-08-09	2025-08-11 15:47:30.373562-05	f
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, spotify_id, vibedrop_username, display_name, email, access_token, refresh_token, expires_at, drop_cred, created_at) FROM stdin;
1	7xw4yczo4i8q0fjnd2ytyu5fd	nickhellmer	\N	\N	BQAKzmJ-uVI-4cDpnWAJburHeLQHI28LIGmOyAHSnyUFyl_FP_KpElo4Jcoi7Hu_VLUUqCx5d0x9S7H1opfw3foIRZfZ2mFZ2Tw6l89vVJBz4LmBNwBlxzd0UK-XRGWy--UAwCztdRnOhbBC7WwZLJ2O95O4hGRP1jgR1dPSggpYK0TcWFOJLDog6viwcTNkOQr2AwPhqzrcp5O_Ro1OcjTz47QQ-xVB2FTYye9s2HrJQb4gqznQ16U42yVuLIMGoqqaAN_AE5HZiFnT1STTpnyu2CJMfxeTS8qk15FmdppEdbwgNuhffg	AQAHczF0WpCtsGZqmGdESxe4yq6KsOEGHiEqRKjpj8lUvFKn1Wd0E2D6ChgV3Jh67HNrtOrovGzxnZIiqSJecDCIlVg2ft9HoaKMTD0-N8kO8CrIPGgN9nIOsmqoJpai0IQ	2025-08-08 22:11:19.383166	5	2025-08-07 14:12:18.625936
\.


--
-- Data for Name: vibe_scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vibe_scores (id, user1_id, user2_id, vibe_index, last_updated) FROM stdin;
\.


--
-- Name: circle_membership_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.circle_membership_id_seq', 9, true);


--
-- Name: song_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.song_feedback_id_seq', 4, true);


--
-- Name: sound_circle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sound_circle_id_seq', 1, true);


--
-- Name: submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.submission_id_seq', 11, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 11, true);


--
-- Name: vibe_score_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vibe_score_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: circle_memberships circle_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_pkey PRIMARY KEY (id);


--
-- Name: song_feedback song_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT song_feedback_pkey PRIMARY KEY (id);


--
-- Name: sound_circles sound_circle_circle_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_circle_name_key UNIQUE (circle_name);


--
-- Name: sound_circles sound_circle_invite_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_invite_code_key UNIQUE (invite_code);


--
-- Name: sound_circles sound_circle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_pkey PRIMARY KEY (id);


--
-- Name: submissions submission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_pkey PRIMARY KEY (id);


--
-- Name: circle_memberships unique_membership; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT unique_membership UNIQUE (user_id, circle_id);


--
-- Name: song_feedback unique_user_song_feedback; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT unique_user_song_feedback UNIQUE (user_id, song_id);


--
-- Name: users user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: users user_spotify_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_spotify_id_key UNIQUE (spotify_id);


--
-- Name: users user_vibedrop_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_vibedrop_username_key UNIQUE (vibedrop_username);


--
-- Name: vibe_scores vibe_score_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_pkey PRIMARY KEY (id);


--
-- Name: circle_memberships circle_membership_circle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_circle_id_fkey FOREIGN KEY (circle_id) REFERENCES public.sound_circles(id);


--
-- Name: circle_memberships circle_membership_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.circle_memberships
    ADD CONSTRAINT circle_membership_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: song_feedback fk_song_feedback__song_id__submission; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT fk_song_feedback__song_id__submission FOREIGN KEY (song_id) REFERENCES public.submissions(id);


--
-- Name: song_feedback fk_song_feedback__user_id__user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT fk_song_feedback__user_id__user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: song_feedback song_feedback_song_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT song_feedback_song_id_fkey FOREIGN KEY (song_id) REFERENCES public.submissions(id);


--
-- Name: song_feedback song_feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.song_feedback
    ADD CONSTRAINT song_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sound_circles sound_circle_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sound_circles
    ADD CONSTRAINT sound_circle_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: submissions submission_circle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_circle_id_fkey FOREIGN KEY (circle_id) REFERENCES public.sound_circles(id);


--
-- Name: submissions submission_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submission_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: vibe_scores vibe_score_user1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_user1_id_fkey FOREIGN KEY (user1_id) REFERENCES public.users(id);


--
-- Name: vibe_scores vibe_score_user2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vibe_scores
    ADD CONSTRAINT vibe_score_user2_id_fkey FOREIGN KEY (user2_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

