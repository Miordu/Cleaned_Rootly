--
-- PostgreSQL database dump
--

-- Dumped from database version 11.4
-- Dumped by pg_dump version 11.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE ONLY public.melons DROP CONSTRAINT melons_melon_type_id_fkey;
ALTER TABLE ONLY public.types DROP CONSTRAINT types_pkey;
ALTER TABLE ONLY public.melons DROP CONSTRAINT melons_pkey;
ALTER TABLE public.types ALTER COLUMN type_id DROP DEFAULT;
DROP SEQUENCE public.types_type_id_seq;
DROP TABLE public.types;
DROP TABLE public.melons;
SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: melons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.melons (
    melon_code character varying(8) NOT NULL,
    name character varying NOT NULL,
    price double precision NOT NULL,
    image_url character varying NOT NULL,
    color character varying NOT NULL,
    seedless boolean NOT NULL,
    melon_type_id integer
);


--
-- Name: types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.types (
    type_id integer NOT NULL,
    name character varying NOT NULL
);


--
-- Name: types_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.types_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: types_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.types_type_id_seq OWNED BY public.types.type_id;


--
-- Name: types type_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.types ALTER COLUMN type_id SET DEFAULT nextval('public.types_type_id_seq'::regclass);


--
-- Data for Name: melons; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.melons (melon_code, name, price, image_url, color, seedless, melon_type_id) FROM stdin;
cren	Crenshaw	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/crenshaw.png	green	t	1
alib	Ali Baba Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/alibaba.webp	green	t	2
anci	Ancient Watermelon	3	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/ancient-watermelon.webp	green	f	2
arkb	Arkansas Black Watermelon	4	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/arkansas-black.jpeg	black	t	2
chrc	Chris Cross Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/chris-cross.jpeg	green	f	2
cong	Congo Watermelon	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/congo-watermelon.webp	green	t	2
cris	Crimson Sweet Watermelon	1.75	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/crimson-sweet.webp	green	f	2
desk	Desert King Watermelon	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/desert-king.jpeg	green	t	2
dixq	Dixie Queen Watermelon	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/dixie-queen.gif	green	f	2
fair	Fairfax Watermelon	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/fairfax-watermelon.jpeg	green	f	2
golh	Golden Honey Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/golden-honey.jpeg	green	t	2
golm	Golden Midget Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/golden-midget.jpeg	gold	f	2
hopy	Hopi Yellow Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/hopi-yellow.webp	gold	t	2
irig	Irish Grey Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/irish-grey.jpg	green	f	2
jubb	Jubilee Bush Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/jubilee-bush.jpeg	green	t	2
jubi	Jubilee Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/jubilee.webp	green	f	2
ledm	Ledmon Watermelon	3	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/ledmon.jpeg	green	t	2
mala	Malali Watermelon	2	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/malali.png	green	f	2
meli	Melitopolski Watermelon	3	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/melitopolski.jpeg	green	t	2
monm	Montenegro Man Melon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/montenegro.jpeg	green	f	2
moos	Moon and Stars Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/moon-and-stars.webp	green	f	2
moon	Moonbeam Watermelon	2.25	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/moonbeam.jpeg	green	t	2
navw	Navajo Winter Watermelon	3	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/navajo-winter.jpeg	green	t	2
oran	Orangeglo Watermelon	2.75	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/orangeglo.jpeg	white	f	2
royg	Royal Golden Watermelon	2.25	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/royal-golden.jpeg	gold	t	2
scab	Scaly Bark Watermelon	4	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/scaly-bark.jpeg	green	t	2
stom	Stone Mountain Watermelon	3	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/stone-mountain.jpeg	green	f	2
sugb	Sugar Baby Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/sugar-baby.jpeg	green	t	2
takg	Takii Gem Watermelon	2.75	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/takii-gem-watermelon.webp	green	f	2
tend	Tendergold Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/tender-gold.webp	green	t	2
texg	Texas Golden Watermelon	2.75	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/texas_golden.jpeg	green	f	2
thrd	Thai Rom Dao Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/thai-rom-dao.webp	green	t	2
tomw	Tom Watson Watermelon	2.25	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/tom-watson.png	green	f	2
whiw	White Wonder Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/white-wonder.png	green	t	2
wils	Wilsons Sweet Watermelon	2.5	https://fellowship.hackbrightacademy.com/materials/exercises/images/melons/wilson-sweet.jpeg	green	f	2
\.


--
-- Data for Name: types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.types (type_id, name) FROM stdin;
1	Hybrid
2	Watermelon
\.


--
-- Name: types_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.types_type_id_seq', 2, true);


--
-- Name: melons melons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.melons
    ADD CONSTRAINT melons_pkey PRIMARY KEY (melon_code);


--
-- Name: types types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.types
    ADD CONSTRAINT types_pkey PRIMARY KEY (type_id);


--
-- Name: melons melons_melon_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.melons
    ADD CONSTRAINT melons_melon_type_id_fkey FOREIGN KEY (melon_type_id) REFERENCES public.types(type_id);


--
-- PostgreSQL database dump complete
--
