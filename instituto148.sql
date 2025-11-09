-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 09-11-2025 a las 22:12:31
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `instituto148`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `aprobaciones`
--

CREATE TABLE `aprobaciones` (
  `id_aprobacion` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `aprobada` int(1) NOT NULL DEFAULT 0,
  `nota` decimal(4,2) DEFAULT 0.00,
  `dni_profesor` int(12) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `aprobaciones`
--

INSERT INTO `aprobaciones` (`id_aprobacion`, `id_usuario`, `id_materia`, `aprobada`, `nota`, `dni_profesor`) VALUES
(8, 4, 7, 1, 1.00, 1000000),
(13, 4, 1, 1, 10.00, 1000000);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ceses`
--

CREATE TABLE `ceses` (
  `id_cese` int(11) NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `fecha` date NOT NULL,
  `motivo` enum('Jubilación','Renuncia','Fallecimiento','Otros') NOT NULL,
  `anio` enum('1°','2°','3°','4°') DEFAULT NULL,
  `hs_modulos` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `id_materia` int(11) NOT NULL,
  `observaciones` text DEFAULT NULL,
  `id_carrera` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `correlativas`
--

CREATE TABLE `correlativas` (
  `id_materia` int(11) NOT NULL,
  `id_materia_correlativa` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `correlativas`
--

INSERT INTO `correlativas` (`id_materia`, `id_materia_correlativa`) VALUES
(9, 5),
(9, 7),
(10, 5),
(10, 7),
(11, 6),
(11, 8),
(12, 1),
(13, 4),
(14, 3),
(15, 3),
(16, 8),
(17, 11),
(17, 14),
(17, 15),
(17, 16),
(18, 5),
(18, 15),
(19, 16),
(21, 12),
(23, 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `estado_civil`
--

CREATE TABLE `estado_civil` (
  `id_estado_civil` int(100) NOT NULL,
  `nombre` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `estado_civil`
--

INSERT INTO `estado_civil` (`id_estado_civil`, `nombre`) VALUES
(1, 'Soltero/a'),
(2, 'Casado/a'),
(3, 'Divorciado/a'),
(4, 'Viudo/a');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inasistencias`
--

CREATE TABLE `inasistencias` (
  `id_inasistencia` int(11) NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `fecha` date NOT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `id_carrera` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `presente` enum('Presente','Ausente') NOT NULL,
  `observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inscripciones_carreras`
--

CREATE TABLE `inscripciones_carreras` (
  `id_inscripcion` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `id_carrera` int(11) NOT NULL,
  `fecha_inscripcion` date NOT NULL,
  `turno` int(11) NOT NULL,
  `estado_alumno` varchar(100) NOT NULL,
  `activo` int(11) NOT NULL,
  `id_turno` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `inscripciones_carreras`
--

INSERT INTO `inscripciones_carreras` (`id_inscripcion`, `id_usuario`, `id_carrera`, `fecha_inscripcion`, `turno`, `estado_alumno`, `activo`, `id_turno`) VALUES
(1, 1, 7, '2024-10-26', 7, 'inscripto', 1, NULL),
(58, 1, 1, '2025-09-07', 1, 'pre_inscripto', 1, 1),
(59, 26, 7, '2025-09-07', 7, 'inscripto', 1, NULL),
(60, 2, 1, '2025-09-12', 1, 'pre_inscripto', 1, 1),
(61, 27, 1, '2025-09-12', 1, 'inscripto', 1, 1),
(62, 4, 1, '2025-09-12', 1, 'inscripto', 1, 1),
(63, 3, 1, '2025-09-23', 1, 'pre_inscripto', 1, 1),
(64, 28, 1, '2025-09-23', 1, 'inscripto', 1, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inscripcion_f`
--

CREATE TABLE `inscripcion_f` (
  `id_inscripcion_final` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `id_mesa` int(11) NOT NULL,
  `fecha_inscripcion` datetime NOT NULL DEFAULT current_timestamp(),
  `estado` varchar(100) NOT NULL DEFAULT 'inscripto'
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `institutos`
--

CREATE TABLE `institutos` (
  `id_instituto` int(11) NOT NULL,
  `nombre_instituto` varchar(100) NOT NULL,
  `telefono` bigint(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `institutos`
--

INSERT INTO `institutos` (`id_instituto`, `nombre_instituto`, `telefono`) VALUES
(1, 'Instituto Superior de Formación Docente y Técnica nº 148 \"Rafael Hernandez\"', 2396474909);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `instituto_usuario`
--

CREATE TABLE `instituto_usuario` (
  `id_instituto_usuario` int(100) NOT NULL,
  `id_instituto` int(100) NOT NULL,
  `id_usuario` int(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `instituto_usuario`
--

INSERT INTO `instituto_usuario` (`id_instituto_usuario`, `id_instituto`, `id_usuario`) VALUES
(1, 1, 1),
(14, 1, 26),
(15, 1, 27),
(17, 1, 4),
(18, 1, 5),
(19, 1, 6),
(20, 1, 28);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `intentos_materia`
--

CREATE TABLE `intentos_materia` (
  `id_intento` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `intentos_restantes` int(11) NOT NULL DEFAULT 4
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `licencias`
--

CREATE TABLE `licencias` (
  `id_licencia` int(11) NOT NULL,
  `dni_profesor` int(11) NOT NULL,
  `desde` date NOT NULL,
  `hasta` date DEFAULT NULL,
  `id_carrera` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `licencia` enum('Licencia administrativa','Licencia médica','Ausente') NOT NULL,
  `tiempo_estimado` enum('Menos de 30 días','Menor a 4 meses','Mayor a 4 meses','Difícil cobertura') NOT NULL,
  `observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `lista_carreras`
--

CREATE TABLE `lista_carreras` (
  `id_carrera` int(11) NOT NULL,
  `id_instituto` int(100) NOT NULL,
  `id_turno` int(11) NOT NULL DEFAULT 1,
  `nombre` varchar(100) NOT NULL,
  `estado` int(11) NOT NULL,
  `año_cursada` int(11) NOT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `lista_carreras`
--

INSERT INTO `lista_carreras` (`id_carrera`, `id_instituto`, `id_turno`, `nombre`, `estado`, `año_cursada`, `activo`) VALUES
(1, 1, 1, 'Análisis de sistemas', 1, 2025, 1),
(2, 1, 1, 'Produccíon agrícola ganadera', 1, 2025, 1),
(3, 1, 1, 'Profesorado de biología', 1, 2025, 1),
(4, 1, 1, 'Profesorado de economía y gestion', 1, 2025, 1),
(5, 1, 1, 'Profesorado de física', 1, 2025, 1),
(6, 1, 1, 'Profesorado de geografía', 1, 2025, 1),
(7, 1, 1, 'Profesorado de historia', 1, 2025, 1),
(8, 1, 1, 'Profesorado de lengua y literatura', 1, 2025, 1),
(9, 1, 1, 'Profesorado de psicología', 1, 2025, 1),
(10, 1, 1, 'Profesorado de química', 1, 2025, 1),
(11, 1, 1, 'Profesorado de matemática', 1, 2025, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `materias`
--

CREATE TABLE `materias` (
  `id_materia` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `id_carrera` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `materias`
--

INSERT INTO `materias` (`id_materia`, `nombre`, `id_carrera`) VALUES
(1, 'Arquitectura de las Computadoras', 1),
(2, 'Ciencia Tecnologia y Sociedad', 1),
(3, 'Algoritmos y Estructuras de datos 1', 1),
(4, 'Inglés 1', 1),
(5, 'Análisis Matemático 1', 1),
(6, 'Prácticas Profesionalizantes 1', 1),
(7, 'Algebra', 1),
(8, 'Sistemas y Organizaciones', 1),
(9, 'Análisis Matemático 2', 1),
(10, 'Estadística', 1),
(11, 'Prácticas Profesionalizantes 2', 1),
(12, 'Sistemas Operativos', 1),
(13, 'Inglés 2', 1),
(14, 'Base de Datos', 1),
(15, 'Algoritmos y Estructuras de datos 2', 1),
(16, 'Ingeniería de Software 1', 1),
(17, 'Prácticas Profesionalizantes 3', 1),
(18, 'Algoritmos y Estructuras de datos 3', 1),
(19, 'Ingeniería de Software 2', 1),
(20, 'Aspectos Legales', 1),
(21, 'Redes y Telecomunicaciones', 1),
(22, 'Seminario', 1),
(23, 'Inglés 3', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mensajes`
--

CREATE TABLE `mensajes` (
  `id_mensaje` int(100) NOT NULL,
  `mensaje` text NOT NULL,
  `id_usuario` int(100) NOT NULL,
  `dia` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mesas_f`
--

CREATE TABLE `mesas_f` (
  `id_mesa` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `fecha_examen` datetime NOT NULL,
  `fecha_apertura` datetime NOT NULL,
  `fecha_cierre` datetime NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `dni_suplente` int(12) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `paises`
--

CREATE TABLE `paises` (
  `id_pais` int(100) NOT NULL,
  `abreviatura` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `paises`
--

INSERT INTO `paises` (`id_pais`, `abreviatura`, `nombre`) VALUES
(1, 'AR', 'Argentina'),
(2, 'AX', 'Islas Gland'),
(3, 'AL', 'Albania'),
(4, 'DE', 'Alemania'),
(5, 'AD', 'Andorra'),
(6, 'AO', 'Angola'),
(7, 'AI', 'Anguilla'),
(8, 'AQ', 'Antártida'),
(9, 'AG', 'Antigua y Barbuda'),
(10, 'AN', 'Antillas Holandesas'),
(11, 'SA', 'Arabia Saudí'),
(12, 'DZ', 'Argelia'),
(13, 'AF', 'Afganistán'),
(14, 'AM', 'Armenia'),
(15, 'AW', 'Aruba'),
(16, 'AU', 'Australia'),
(17, 'AT', 'Austria'),
(18, 'AZ', 'Azerbaiyán'),
(19, 'BS', 'Bahamas'),
(20, 'BH', 'Bahréin'),
(21, 'BD', 'Bangladesh'),
(22, 'BB', 'Barbados'),
(23, 'BY', 'Bielorrusia'),
(24, 'BE', 'Bélgica'),
(25, 'BZ', 'Belice'),
(26, 'BJ', 'Benin'),
(27, 'BM', 'Bermudas'),
(28, 'BT', 'Bhután'),
(29, 'BO', 'Bolivia'),
(30, 'BA', 'Bosnia y Herzegovina'),
(31, 'BW', 'Botsuana'),
(32, 'BV', 'Isla Bouvet'),
(33, 'BR', 'Brasil'),
(34, 'BN', 'Brunéi'),
(35, 'BG', 'Bulgaria'),
(36, 'BF', 'Burkina Faso'),
(37, 'BI', 'Burundi'),
(38, 'CV', 'Cabo Verde'),
(39, 'KY', 'Islas Caimán'),
(40, 'KH', 'Camboya'),
(41, 'CM', 'Camerún'),
(42, 'CA', 'Canadá'),
(43, 'CF', 'República Centroafricana'),
(44, 'TD', 'Chad'),
(45, 'CZ', 'República Checa'),
(46, 'CL', 'Chile'),
(47, 'CN', 'China'),
(48, 'CY', 'Chipre'),
(49, 'CX', 'Isla de Navidad'),
(50, 'VA', 'Ciudad del Vaticano'),
(51, 'CC', 'Islas Cocos'),
(52, 'CO', 'Colombia'),
(53, 'KM', 'Comoras'),
(54, 'CD', 'República Democrática del Congo'),
(55, 'CG', 'Congo'),
(56, 'CK', 'Islas Cook'),
(57, 'KP', 'Corea del Norte'),
(58, 'KR', 'Corea del Sur'),
(59, 'CI', 'Costa de Marfil'),
(60, 'CR', 'Costa Rica'),
(61, 'HR', 'Croacia'),
(62, 'CU', 'Cuba'),
(63, 'DK', 'Dinamarca'),
(64, 'DM', 'Dominica'),
(65, 'DO', 'República Dominicana'),
(66, 'EC', 'Ecuador'),
(67, 'EG', 'Egipto'),
(68, 'SV', 'El Salvador'),
(69, 'AE', 'Emiratos Árabes Unidos'),
(70, 'ER', 'Eritrea'),
(71, 'SK', 'Eslovaquia'),
(72, 'SI', 'Eslovenia'),
(73, 'ES', 'España'),
(74, 'UM', 'Islas ultramarinas de Estados Unidos'),
(75, 'US', 'Estados Unidos'),
(76, 'EE', 'Estonia'),
(77, 'ET', 'Etiopía'),
(78, 'FO', 'Islas Feroe'),
(79, 'PH', 'Filipinas'),
(80, 'FI', 'Finlandia'),
(81, 'FJ', 'Fiyi'),
(82, 'FR', 'Francia'),
(83, 'GA', 'Gabón'),
(84, 'GM', 'Gambia'),
(85, 'GE', 'Georgia'),
(86, 'GS', 'Islas Georgias del Sur y Sandwich del Sur'),
(87, 'GH', 'Ghana'),
(88, 'GI', 'Gibraltar'),
(89, 'GD', 'Granada'),
(90, 'GR', 'Grecia'),
(91, 'GL', 'Groenlandia'),
(92, 'GP', 'Guadalupe'),
(93, 'GU', 'Guam'),
(94, 'GT', 'Guatemala'),
(95, 'GF', 'Guayana Francesa'),
(96, 'GN', 'Guinea'),
(97, 'GQ', 'Guinea Ecuatorial'),
(98, 'GW', 'Guinea-Bissau'),
(99, 'GY', 'Guyana'),
(100, 'HT', 'Haití'),
(101, 'HM', 'Islas Heard y McDonald'),
(102, 'HN', 'Honduras'),
(103, 'HK', 'Hong Kong'),
(104, 'HU', 'Hungría'),
(105, 'IN', 'India'),
(106, 'ID', 'Indonesia'),
(107, 'IR', 'Irán'),
(108, 'IQ', 'Iraq'),
(109, 'IE', 'Irlanda'),
(110, 'IS', 'Islandia'),
(111, 'IL', 'Israel'),
(112, 'IT', 'Italia'),
(113, 'JM', 'Jamaica'),
(114, 'JP', 'Japón'),
(115, 'JO', 'Jordania'),
(116, 'KZ', 'Kazajstán'),
(117, 'KE', 'Kenia'),
(118, 'KG', 'Kirguistán'),
(119, 'KI', 'Kiribati'),
(120, 'KW', 'Kuwait'),
(121, 'LA', 'Laos'),
(122, 'LS', 'Lesotho'),
(123, 'LV', 'Letonia'),
(124, 'LB', 'Líbano'),
(125, 'LR', 'Liberia'),
(126, 'LY', 'Libia'),
(127, 'LI', 'Liechtenstein'),
(128, 'LT', 'Lituania'),
(129, 'LU', 'Luxemburgo'),
(130, 'MO', 'Macao'),
(131, 'MK', 'ARY Macedonia'),
(132, 'MG', 'Madagascar'),
(133, 'MY', 'Malasia'),
(134, 'MW', 'Malawi'),
(135, 'MV', 'Maldivas'),
(136, 'ML', 'Malí'),
(137, 'MT', 'Malta'),
(138, 'FK', 'Islas Malvinas'),
(139, 'MP', 'Islas Marianas del Norte'),
(140, 'MA', 'Marruecos'),
(141, 'MH', 'Islas Marshall'),
(142, 'MQ', 'Martinica'),
(143, 'MU', 'Mauricio'),
(144, 'MR', 'Mauritania'),
(145, 'YT', 'Mayotte'),
(146, 'MX', 'México'),
(147, 'FM', 'Micronesia'),
(148, 'MD', 'Moldavia'),
(149, 'MC', 'Mónaco'),
(150, 'MN', 'Mongolia'),
(151, 'MS', 'Montserrat'),
(152, 'MZ', 'Mozambique'),
(153, 'MM', 'Myanmar'),
(154, 'NA', 'Namibia'),
(155, 'NR', 'Nauru'),
(156, 'NP', 'Nepal'),
(157, 'NI', 'Nicaragua'),
(158, 'NE', 'Níger'),
(159, 'NG', 'Nigeria'),
(160, 'NU', 'Niue'),
(161, 'NF', 'Isla Norfolk'),
(162, 'NO', 'Noruega'),
(163, 'NC', 'Nueva Caledonia'),
(164, 'NZ', 'Nueva Zelanda'),
(165, 'OM', 'Omán'),
(166, 'NL', 'Países Bajos'),
(167, 'PK', 'Pakistán'),
(168, 'PW', 'Palau'),
(169, 'PS', 'Palestina'),
(170, 'PA', 'Panamá'),
(171, 'PG', 'Papúa Nueva Guinea'),
(172, 'PY', 'Paraguay'),
(173, 'PE', 'Perú'),
(174, 'PN', 'Islas Pitcairn'),
(175, 'PF', 'Polinesia Francesa'),
(176, 'PL', 'Polonia'),
(177, 'PT', 'Portugal'),
(178, 'PR', 'Puerto Rico'),
(179, 'QA', 'Qatar'),
(180, 'GB', 'Reino Unido'),
(181, 'RE', 'Reunión'),
(182, 'RW', 'Ruanda'),
(183, 'RO', 'Rumania'),
(184, 'RU', 'Rusia'),
(185, 'EH', 'Sahara Occidental'),
(186, 'SB', 'Islas Salomón'),
(187, 'WS', 'Samoa'),
(188, 'AS', 'Samoa Americana'),
(189, 'KN', 'San Cristóbal y Nevis'),
(190, 'SM', 'San Marino'),
(191, 'PM', 'San Pedro y Miquelón'),
(192, 'VC', 'San Vicente y las Granadinas'),
(193, 'SH', 'Santa Helena'),
(194, 'LC', 'Santa Lucía'),
(195, 'ST', 'Santo Tomé y Príncipe'),
(196, 'SN', 'Senegal'),
(197, 'CS', 'Serbia y Montenegro'),
(198, 'SC', 'Seychelles'),
(199, 'SL', 'Sierra Leona'),
(200, 'SG', 'Singapur'),
(201, 'SY', 'Siria'),
(202, 'SO', 'Somalia'),
(203, 'LK', 'Sri Lanka'),
(204, 'SZ', 'Suazilandia'),
(205, 'ZA', 'Sudáfrica'),
(206, 'SD', 'Sudán'),
(207, 'SE', 'Suecia'),
(208, 'CH', 'Suiza'),
(209, 'SR', 'Surinam'),
(210, 'SJ', 'Svalbard y Jan Mayen'),
(211, 'TH', 'Tailandia'),
(212, 'TW', 'Taiwán'),
(213, 'TZ', 'Tanzania'),
(214, 'TJ', 'Tayikistán'),
(215, 'IO', 'Territorio Británico del Océano Índico'),
(216, 'TF', 'Territorios Australes Franceses'),
(217, 'TL', 'Timor Oriental'),
(218, 'TG', 'Togo'),
(219, 'TK', 'Tokelau'),
(220, 'TO', 'Tonga'),
(221, 'TT', 'Trinidad y Tobago'),
(222, 'TN', 'Túnez'),
(223, 'TC', 'Islas Turcas y Caicos'),
(224, 'TM', 'Turkmenistán'),
(225, 'TR', 'Turquía'),
(226, 'TV', 'Tuvalu'),
(227, 'UA', 'Ucrania'),
(228, 'UG', 'Uganda'),
(229, 'UY', 'Uruguay'),
(230, 'UZ', 'Uzbekistán'),
(231, 'VU', 'Vanuatu'),
(232, 'VE', 'Venezuela'),
(233, 'VN', 'Vietnam'),
(234, 'VG', 'Islas Vírgenes Británicas'),
(235, 'VI', 'Islas Vírgenes de los Estados Unidos'),
(236, 'WF', 'Wallis y Futuna'),
(237, 'YE', 'Yemen'),
(238, 'DJ', 'Yibuti'),
(239, 'ZM', 'Zambia'),
(240, 'ZW', 'Zimbabue');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `perfiles`
--

CREATE TABLE `perfiles` (
  `id_perfil` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `perfiles`
--

INSERT INTO `perfiles` (`id_perfil`, `nombre`, `descripcion`) VALUES
(1, 'Directivo', ''),
(2, 'Preceptor', ''),
(3, 'Profesores', ''),
(4, 'Alumnos', '');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `perfiles_usuarios`
--

CREATE TABLE `perfiles_usuarios` (
  `id_perfiles_usuarios` int(11) NOT NULL,
  `id_perfil` int(11) NOT NULL,
  `id_usuarios` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `perfiles_usuarios`
--

INSERT INTO `perfiles_usuarios` (`id_perfiles_usuarios`, `id_perfil`, `id_usuarios`) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 3, 1),
(4, 4, 1),
(27, 4, 26),
(28, 4, 27),
(29, 4, 4),
(30, 1, 5),
(31, 2, 6),
(32, 4, 28);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `permisos`
--

CREATE TABLE `permisos` (
  `id_permiso` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `permisos`
--

INSERT INTO `permisos` (`id_permiso`, `nombre`, `descripcion`) VALUES
(1, '', 'puede ver el dashboard'),
(2, '', 'puede inscribir alumnos'),
(3, '', 'puede modificar alumnos'),
(4, '', 'puede eliminar alumnos'),
(5, '', 'puede egresar alumnos'),
(6, '', 'puede inscribir profesores'),
(7, '', 'puede modificar profesores'),
(8, '', 'puede eliminar profesores'),
(9, '', 'puede visualizar los alumnos que tiene en sus materias'),
(10, '', 'puede ver los horarios de sus materias'),
(11, '', 'puede ver los horarios en los que cursa'),
(12, '', 'puede agregar carreras'),
(13, '', 'puede modificar carreras'),
(14, '', 'puede eliminar carreras'),
(15, '', 'puede ver las carreras que cursa'),
(16, '', 'puede agregar materias'),
(17, '', 'puede modificar materias'),
(18, '', 'puede eliminar materias'),
(19, '', 'puede enviar mensajes a home'),
(20, '', 'puede ver los mensajes a home'),
(21, '', 'puede visualizar el modulo pre-inscripcion'),
(22, '', 'puede visualizar el modulo alumnos'),
(23, '', 'puede visualizar el modulo profesores'),
(24, '', 'puede visualizar el modulo carreras'),
(25, '', 'puede visualizar el modulo horarios'),
(26, '', 'puede visualizar el modulo secretaria'),
(27, '', 'puede visualizar el modulo reportes'),
(28, '', 'Finales alumno'),
(29, 'crear_final', 'Crear finales para carreras');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `permisos_perfiles`
--

CREATE TABLE `permisos_perfiles` (
  `id_permisos_perfiles` int(11) NOT NULL,
  `id_perfil` int(100) NOT NULL,
  `Id_permisos` int(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `permisos_perfiles`
--

INSERT INTO `permisos_perfiles` (`id_permisos_perfiles`, `id_perfil`, `Id_permisos`) VALUES
(2, 1, 2),
(3, 1, 3),
(4, 1, 4),
(5, 1, 5),
(6, 1, 6),
(7, 1, 7),
(8, 1, 8),
(9, 1, 9),
(10, 1, 10),
(11, 1, 11),
(12, 1, 12),
(13, 1, 13),
(14, 1, 14),
(15, 1, 15),
(16, 1, 16),
(17, 1, 17),
(18, 1, 18),
(19, 1, 19),
(20, 1, 20),
(21, 1, 21),
(22, 1, 22),
(23, 1, 23),
(24, 1, 24),
(25, 1, 25),
(26, 1, 26),
(27, 1, 27),
(28, 2, 1),
(29, 2, 2),
(30, 2, 3),
(31, 2, 4),
(32, 2, 5),
(33, 2, 6),
(34, 2, 7),
(35, 2, 8),
(36, 2, 12),
(37, 2, 13),
(38, 2, 14),
(39, 2, 15),
(40, 2, 16),
(41, 2, 17),
(42, 2, 18),
(43, 2, 19),
(44, 2, 20),
(45, 2, 21),
(46, 2, 22),
(47, 2, 24),
(48, 2, 26),
(49, 2, 27),
(50, 3, 1),
(52, 3, 9),
(53, 3, 10),
(54, 3, 20),
(55, 3, 22),
(56, 3, 23),
(57, 3, 25),
(58, 4, 1),
(59, 4, 11),
(60, 4, 15),
(61, 4, 20),
(62, 4, 22),
(63, 4, 25),
(64, 1, 1),
(65, 2, 25),
(66, 2, 23),
(67, 2, 22),
(68, 4, 28),
(70, 4, 28),
(71, 1, 29),
(72, 2, 29);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pre_inscripciones`
--

CREATE TABLE `pre_inscripciones` (
  `id_usuario` int(8) NOT NULL,
  `dni` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `id_sexo` int(10) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `lugar_nacimiento` varchar(100) DEFAULT NULL,
  `id_estado_civil` int(100) NOT NULL,
  `cantidad_hijos` int(100) NOT NULL,
  `familiares_a_cargo` int(11) NOT NULL,
  `domicilio` varchar(100) NOT NULL,
  `piso` varchar(50) NOT NULL,
  `id_pais` int(20) NOT NULL,
  `id_provincia` int(100) NOT NULL,
  `codigo_postal` varchar(100) NOT NULL,
  `telefono` bigint(200) NOT NULL,
  `telefono_alt` bigint(200) DEFAULT NULL,
  `telefono_alt_propietario` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `titulo_base` varchar(100) NOT NULL,
  `anio_egreso` int(100) NOT NULL,
  `id_institucion` int(100) NOT NULL,
  `otros_estudios` varchar(100) DEFAULT NULL,
  `anio_egreso_otros` int(100) DEFAULT NULL,
  `trabaja` varchar(100) NOT NULL,
  `actividad` varchar(100) DEFAULT NULL,
  `horario_habitual` varchar(100) DEFAULT NULL,
  `obra_social` varchar(100) DEFAULT NULL,
  `pass` varchar(100) NOT NULL DEFAULT '12345678',
  `activo` int(1) NOT NULL DEFAULT 1,
  `localidad` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `profesores`
--

CREATE TABLE `profesores` (
  `id_profesor` int(11) NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `lugar_nacimiento` varchar(100) DEFAULT NULL,
  `pais` varchar(100) DEFAULT NULL,
  `foja` varchar(50) DEFAULT NULL,
  `n_registro` varchar(50) DEFAULT NULL,
  `certificado_aptitud_fisica` tinyint(1) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  `celular` varchar(20) DEFAULT NULL,
  `piso` int(11) DEFAULT NULL,
  `dpto` varchar(10) DEFAULT NULL,
  `codigo_postal` int(11) DEFAULT NULL,
  `partido` varchar(100) DEFAULT NULL,
  `sexo` varchar(20) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `domicilio` varchar(255) DEFAULT NULL,
  `localidad` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `profesores`
--

INSERT INTO `profesores` (`id_profesor`, `dni_profesor`, `nombre`, `apellido`, `email`, `fecha_nacimiento`, `lugar_nacimiento`, `pais`, `foja`, `n_registro`, `certificado_aptitud_fisica`, `telefono`, `celular`, `piso`, `dpto`, `codigo_postal`, `partido`, `sexo`, `activo`, `domicilio`, `localidad`) VALUES
(16, 1000000, 'Gustavo', 'Trinitario', 'gustavotrinitario@yahoo.com', '1974-02-14', '9 de febrero', 'Argentina', '1', '1', 1, '555555', '5555556', NULL, NULL, 6450, 'Pehuajo', 'Hombre', 1, 'No se', 'Pehuajo'),
(17, 2000000, 'Claudio', 'Perlo', 'Claudioperlo@gmail.com', '1977-03-10', 'Buenos aires', 'Argentina', '2', '2', 1, '54342145645667', '11111111111', NULL, NULL, 6450, 'Pehuajo', 'Hombre', 1, 'No se', 'Pehuajo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `provincias`
--

CREATE TABLE `provincias` (
  `id_provincia` int(100) NOT NULL,
  `id_pais` int(100) NOT NULL,
  `nombre` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `provincias`
--

INSERT INTO `provincias` (`id_provincia`, `id_pais`, `nombre`) VALUES
(2, 1, 'Buenos Aires'),
(3, 1, 'Catamara'),
(4, 1, 'Córdoba'),
(5, 1, 'Corrientes'),
(6, 1, 'Entre Ríos'),
(7, 1, 'Jujuy'),
(8, 1, 'Mendoza'),
(9, 1, 'La Rioja'),
(10, 1, 'Salta'),
(11, 1, 'San Juan'),
(12, 1, 'San Luis'),
(13, 1, 'Santa Fe'),
(14, 1, 'Santiago del Estero'),
(15, 1, 'Tucumán'),
(16, 1, 'Chaco'),
(17, 1, 'Chubut'),
(18, 1, 'Formosa'),
(19, 1, 'Misiones'),
(20, 1, 'Neuquén'),
(21, 1, 'La Pampa'),
(22, 1, 'Río Negro'),
(23, 1, 'Santa Cruz'),
(24, 1, 'Tierra del Fuego');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `sexos`
--

CREATE TABLE `sexos` (
  `id_sexo` int(100) NOT NULL,
  `descripcion` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `sexos`
--

INSERT INTO `sexos` (`id_sexo`, `descripcion`) VALUES
(1, 'Hombre'),
(2, 'Mujer'),
(3, 'Otro');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `suplencias`
--

CREATE TABLE `suplencias` (
  `id_suplencia` int(11) NOT NULL,
  `dni_profesor` int(11) NOT NULL,
  `dni_suplente` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `id_carrera` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `modulos` int(11) NOT NULL,
  `fecha_desde` date NOT NULL,
  `fecha_hasta` date NOT NULL,
  `observaciones` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `titulos_profesores`
--

CREATE TABLE `titulos_profesores` (
  `id_titulo` int(11) NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `titulo` varchar(100) NOT NULL,
  `expedido_por` varchar(100) NOT NULL,
  `duracion` varchar(50) DEFAULT NULL,
  `finalizo` int(1) DEFAULT 1,
  `fecha_egreso` date DEFAULT NULL,
  `porcentaje_carrera` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `titulos_profesores`
--

INSERT INTO `titulos_profesores` (`id_titulo`, `dni_profesor`, `titulo`, `expedido_por`, `duracion`, `finalizo`, `fecha_egreso`, `porcentaje_carrera`) VALUES
(8, 1000000, 'Certificacion Cisco de base de datos', 'Rafael Surquiza', '5', 1, '2005-06-15', 100.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `toma_posesion`
--

CREATE TABLE `toma_posesion` (
  `id_toma` int(11) NOT NULL,
  `dni_profesor` int(12) NOT NULL,
  `fecha` date NOT NULL,
  `id_carrera` int(11) NOT NULL,
  `id_materia` int(11) NOT NULL,
  `modulos` int(11) NOT NULL,
  `situacion_revista` enum('Titular','Suplente','Provicional','') DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `toma_posesion`
--

INSERT INTO `toma_posesion` (`id_toma`, `dni_profesor`, `fecha`, `id_carrera`, `id_materia`, `modulos`, `situacion_revista`, `observaciones`, `activo`) VALUES
(13, 1000000, '2025-11-07', 1, 14, 55, NULL, NULL, 1),
(14, 2000000, '2025-11-08', 1, 19, 99, NULL, NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_carrera`
--

CREATE TABLE `turno_carrera` (
  `id_turno` int(11) NOT NULL,
  `id_carrera` int(100) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  `estado` int(2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `turno_carrera`
--

INSERT INTO `turno_carrera` (`id_turno`, `id_carrera`, `descripcion`, `estado`) VALUES
(1, 1, 'Tarde', 1),
(2, 2, 'Mañana', 1),
(3, 3, 'Tarde', 1),
(4, 4, 'Tarde', 1),
(5, 5, 'Tarde', 1),
(6, 6, 'Tarde', 1),
(7, 7, 'Tarde', 1),
(8, 8, 'Tarde', 1),
(9, 9, 'Mañana', 1),
(10, 10, 'Tarde', 1),
(11, 11, 'Tarde', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id_usuario` int(50) NOT NULL,
  `dni` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `id_sexo` int(10) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `lugar_nacimiento` varchar(100) NOT NULL,
  `id_estado_civil` int(100) NOT NULL,
  `cantidad_hijos` int(100) NOT NULL,
  `familiares_a_cargo` int(11) NOT NULL,
  `domicilio` varchar(100) NOT NULL,
  `piso` varchar(50) DEFAULT NULL,
  `id_pais` int(20) NOT NULL,
  `id_provincia` int(100) NOT NULL,
  `codigo_postal` varchar(100) NOT NULL,
  `telefono` bigint(200) NOT NULL,
  `telefono_alt` bigint(200) DEFAULT NULL,
  `telefono_alt_propietario` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `titulo_base` varchar(100) NOT NULL,
  `anio_egreso` int(100) NOT NULL,
  `id_institucion` int(100) NOT NULL,
  `otros_estudios` varchar(100) DEFAULT NULL,
  `anio_egreso_otros` int(100) DEFAULT NULL,
  `trabaja` varchar(100) NOT NULL,
  `actividad` varchar(100) DEFAULT NULL,
  `horario_habitual` varchar(100) DEFAULT NULL,
  `obra_social` varchar(100) DEFAULT NULL,
  `pass` varchar(100) NOT NULL,
  `activo` int(1) NOT NULL DEFAULT 1,
  `localidad` varchar(100) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id_usuario`, `dni`, `nombre`, `apellido`, `id_sexo`, `fecha_nacimiento`, `lugar_nacimiento`, `id_estado_civil`, `cantidad_hijos`, `familiares_a_cargo`, `domicilio`, `piso`, `id_pais`, `id_provincia`, `codigo_postal`, `telefono`, `telefono_alt`, `telefono_alt_propietario`, `email`, `titulo_base`, `anio_egreso`, `id_institucion`, `otros_estudios`, `anio_egreso_otros`, `trabaja`, `actividad`, `horario_habitual`, `obra_social`, `pass`, `activo`, `localidad`) VALUES
(1, 1000000, 'Administrador', 'Ejemplo', 1, '2003-11-28', 'Henderson', 1, 0, 0, 'Florida 50', NULL, 1, 2, '6465', 2314532940, 2314478877, 'Madre', 'info@instituto148pehuajo.com.ar', 't', 2019, 2, '', NULL, 'no', NULL, NULL, NULL, '12345678', 1, ''),
(4, 1000003, 'Test', 'Nuevo2', 1, '2000-01-01', 'Buenos Aires', 1, 0, 0, 'Calle Falsa 789', NULL, 1, 1, '1000', 555555555, NULL, NULL, 'test3@ejemplo.com', 'Bachiller', 2016, 1, NULL, NULL, 'no', NULL, NULL, NULL, '12345678', 1, ''),
(5, 2000001, 'Directivo', 'Test', 1, '1970-01-01', 'Buenos Aires', 1, 0, 0, 'Calle Falsa 101', NULL, 1, 1, '1000', 111222333, NULL, NULL, 'directivo@ejemplo.com', 'Licenciatura', 1995, 1, NULL, NULL, 'sí', 'Directivo', '09:00-17:00', NULL, '12345678', 1, ''),
(6, 2000002, 'Secretaria', 'Test', 1, '1980-01-01', 'Buenos Aires', 1, 0, 0, 'Calle Falsa 102', NULL, 1, 1, '1000', 444555666, NULL, NULL, 'secretaria@ejemplo.com', 'Administración', 2000, 1, NULL, NULL, 'sí', 'Secretaría', '08:00-16:00', NULL, '12345678', 1, ''),
(26, 42538479, 'ricardo', 'perotenuto', 1, '2000-03-13', 'Pehuajó', 1, 20, 2, 'Independencia del perú 1005', NULL, 1, 2, '6450', 2396580006, 22568744558, 'mama', 'agustinvaquero3000@gmail.com', 'Bachiller en ciencias sociales', 2019, 1, '', NULL, 'no', NULL, NULL, NULL, '12345678', 1, ''),
(27, 11111111, 'ricardo', 'perotenuto', 1, '2000-03-13', 'Pehuajó', 1, 0, 0, 'Independencia del perú 1005', NULL, 1, 2, '6450', 23965555555, 2256874455555, 'mama', 'agustin@gmail.com', 'prueba', 2000, 1, '', NULL, 'no', NULL, NULL, NULL, '12345678', 1, ''),
(28, 35033250, 'anahi', 'Cano', 2, '1989-02-01', 'Pehuajó', 2, 10, 0, 'maciel 917', '123312', 1, 2, '6450', 123123123, 123124124, '3123123', 'anahi_c@gotmail.com', 'informatica', 2009, 1, '', NULL, 'no', NULL, NULL, NULL, '12345678', 1, '');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `aprobaciones`
--
ALTER TABLE `aprobaciones`
  ADD PRIMARY KEY (`id_aprobacion`),
  ADD UNIQUE KEY `uk_usuario_materia` (`id_usuario`,`id_materia`),
  ADD KEY `id_materia` (`id_materia`);

--
-- Indices de la tabla `ceses`
--
ALTER TABLE `ceses`
  ADD PRIMARY KEY (`id_cese`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `ceses_ibfk_2` (`id_carrera`),
  ADD KEY `ceses_ibfk_3` (`id_materia`);

--
-- Indices de la tabla `correlativas`
--
ALTER TABLE `correlativas`
  ADD PRIMARY KEY (`id_materia`,`id_materia_correlativa`),
  ADD KEY `id_materia_correlativa` (`id_materia_correlativa`);

--
-- Indices de la tabla `estado_civil`
--
ALTER TABLE `estado_civil`
  ADD PRIMARY KEY (`id_estado_civil`);

--
-- Indices de la tabla `inasistencias`
--
ALTER TABLE `inasistencias`
  ADD PRIMARY KEY (`id_inasistencia`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `inasistencias_ibfk_2` (`id_carrera`),
  ADD KEY `inasistencias_ibfk_3` (`id_materia`);

--
-- Indices de la tabla `inscripciones_carreras`
--
ALTER TABLE `inscripciones_carreras`
  ADD PRIMARY KEY (`id_inscripcion`),
  ADD KEY `id_turno` (`id_turno`);

--
-- Indices de la tabla `inscripcion_f`
--
ALTER TABLE `inscripcion_f`
  ADD PRIMARY KEY (`id_inscripcion_final`),
  ADD KEY `id_usuario` (`id_usuario`),
  ADD KEY `id_final` (`id_mesa`);

--
-- Indices de la tabla `institutos`
--
ALTER TABLE `institutos`
  ADD PRIMARY KEY (`id_instituto`);

--
-- Indices de la tabla `instituto_usuario`
--
ALTER TABLE `instituto_usuario`
  ADD PRIMARY KEY (`id_instituto_usuario`);

--
-- Indices de la tabla `intentos_materia`
--
ALTER TABLE `intentos_materia`
  ADD PRIMARY KEY (`id_intento`),
  ADD UNIQUE KEY `uk_usuario_materia` (`id_usuario`,`id_materia`),
  ADD KEY `id_materia` (`id_materia`);

--
-- Indices de la tabla `licencias`
--
ALTER TABLE `licencias`
  ADD PRIMARY KEY (`id_licencia`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `licencias_ibfk_2` (`id_carrera`),
  ADD KEY `licencias_ibfk_3` (`id_materia`);

--
-- Indices de la tabla `lista_carreras`
--
ALTER TABLE `lista_carreras`
  ADD PRIMARY KEY (`id_carrera`),
  ADD KEY `id_turno` (`id_turno`);

--
-- Indices de la tabla `materias`
--
ALTER TABLE `materias`
  ADD PRIMARY KEY (`id_materia`);

--
-- Indices de la tabla `mensajes`
--
ALTER TABLE `mensajes`
  ADD PRIMARY KEY (`id_mensaje`);

--
-- Indices de la tabla `mesas_f`
--
ALTER TABLE `mesas_f`
  ADD PRIMARY KEY (`id_mesa`),
  ADD KEY `id_materia` (`id_materia`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `dni_suplente` (`dni_suplente`);

--
-- Indices de la tabla `paises`
--
ALTER TABLE `paises`
  ADD PRIMARY KEY (`id_pais`);

--
-- Indices de la tabla `perfiles`
--
ALTER TABLE `perfiles`
  ADD PRIMARY KEY (`id_perfil`);

--
-- Indices de la tabla `perfiles_usuarios`
--
ALTER TABLE `perfiles_usuarios`
  ADD PRIMARY KEY (`id_perfiles_usuarios`);

--
-- Indices de la tabla `permisos`
--
ALTER TABLE `permisos`
  ADD PRIMARY KEY (`id_permiso`);

--
-- Indices de la tabla `permisos_perfiles`
--
ALTER TABLE `permisos_perfiles`
  ADD PRIMARY KEY (`id_permisos_perfiles`);

--
-- Indices de la tabla `pre_inscripciones`
--
ALTER TABLE `pre_inscripciones`
  ADD PRIMARY KEY (`id_usuario`);

--
-- Indices de la tabla `profesores`
--
ALTER TABLE `profesores`
  ADD PRIMARY KEY (`id_profesor`),
  ADD UNIQUE KEY `dni` (`dni_profesor`),
  ADD UNIQUE KEY `dni_profesor` (`dni_profesor`),
  ADD UNIQUE KEY `unique_foja` (`foja`),
  ADD UNIQUE KEY `unique_n_registro` (`n_registro`);

--
-- Indices de la tabla `provincias`
--
ALTER TABLE `provincias`
  ADD PRIMARY KEY (`id_provincia`);

--
-- Indices de la tabla `sexos`
--
ALTER TABLE `sexos`
  ADD PRIMARY KEY (`id_sexo`);

--
-- Indices de la tabla `suplencias`
--
ALTER TABLE `suplencias`
  ADD PRIMARY KEY (`id_suplencia`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `id_carrera` (`id_carrera`),
  ADD KEY `id_materia` (`id_materia`),
  ADD KEY `dni_suplente` (`dni_suplente`);

--
-- Indices de la tabla `titulos_profesores`
--
ALTER TABLE `titulos_profesores`
  ADD PRIMARY KEY (`id_titulo`),
  ADD KEY `dni_profesor` (`dni_profesor`);

--
-- Indices de la tabla `toma_posesion`
--
ALTER TABLE `toma_posesion`
  ADD PRIMARY KEY (`id_toma`),
  ADD KEY `dni_profesor` (`dni_profesor`),
  ADD KEY `toma_posesion_ibfk_2` (`id_carrera`),
  ADD KEY `toma_posesion_ibfk_3` (`id_materia`);

--
-- Indices de la tabla `turno_carrera`
--
ALTER TABLE `turno_carrera`
  ADD PRIMARY KEY (`id_turno`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id_usuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `aprobaciones`
--
ALTER TABLE `aprobaciones`
  MODIFY `id_aprobacion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT de la tabla `ceses`
--
ALTER TABLE `ceses`
  MODIFY `id_cese` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `estado_civil`
--
ALTER TABLE `estado_civil`
  MODIFY `id_estado_civil` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `inasistencias`
--
ALTER TABLE `inasistencias`
  MODIFY `id_inasistencia` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `inscripciones_carreras`
--
ALTER TABLE `inscripciones_carreras`
  MODIFY `id_inscripcion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=65;

--
-- AUTO_INCREMENT de la tabla `inscripcion_f`
--
ALTER TABLE `inscripcion_f`
  MODIFY `id_inscripcion_final` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=59;

--
-- AUTO_INCREMENT de la tabla `institutos`
--
ALTER TABLE `institutos`
  MODIFY `id_instituto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `instituto_usuario`
--
ALTER TABLE `instituto_usuario`
  MODIFY `id_instituto_usuario` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT de la tabla `intentos_materia`
--
ALTER TABLE `intentos_materia`
  MODIFY `id_intento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=96;

--
-- AUTO_INCREMENT de la tabla `licencias`
--
ALTER TABLE `licencias`
  MODIFY `id_licencia` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `lista_carreras`
--
ALTER TABLE `lista_carreras`
  MODIFY `id_carrera` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `mensajes`
--
ALTER TABLE `mensajes`
  MODIFY `id_mensaje` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `mesas_f`
--
ALTER TABLE `mesas_f`
  MODIFY `id_mesa` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=62;

--
-- AUTO_INCREMENT de la tabla `paises`
--
ALTER TABLE `paises`
  MODIFY `id_pais` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=241;

--
-- AUTO_INCREMENT de la tabla `perfiles`
--
ALTER TABLE `perfiles`
  MODIFY `id_perfil` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `perfiles_usuarios`
--
ALTER TABLE `perfiles_usuarios`
  MODIFY `id_perfiles_usuarios` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT de la tabla `permisos`
--
ALTER TABLE `permisos`
  MODIFY `id_permiso` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- AUTO_INCREMENT de la tabla `permisos_perfiles`
--
ALTER TABLE `permisos_perfiles`
  MODIFY `id_permisos_perfiles` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=73;

--
-- AUTO_INCREMENT de la tabla `pre_inscripciones`
--
ALTER TABLE `pre_inscripciones`
  MODIFY `id_usuario` int(8) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `profesores`
--
ALTER TABLE `profesores`
  MODIFY `id_profesor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT de la tabla `provincias`
--
ALTER TABLE `provincias`
  MODIFY `id_provincia` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT de la tabla `sexos`
--
ALTER TABLE `sexos`
  MODIFY `id_sexo` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `suplencias`
--
ALTER TABLE `suplencias`
  MODIFY `id_suplencia` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `titulos_profesores`
--
ALTER TABLE `titulos_profesores`
  MODIFY `id_titulo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `toma_posesion`
--
ALTER TABLE `toma_posesion`
  MODIFY `id_toma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `turno_carrera`
--
ALTER TABLE `turno_carrera`
  MODIFY `id_turno` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id_usuario` int(50) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `aprobaciones`
--
ALTER TABLE `aprobaciones`
  ADD CONSTRAINT `aprobaciones_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
  ADD CONSTRAINT `aprobaciones_ibfk_2` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `ceses`
--
ALTER TABLE `ceses`
  ADD CONSTRAINT `ceses_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`),
  ADD CONSTRAINT `ceses_ibfk_2` FOREIGN KEY (`id_carrera`) REFERENCES `lista_carreras` (`id_carrera`),
  ADD CONSTRAINT `ceses_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `correlativas`
--
ALTER TABLE `correlativas`
  ADD CONSTRAINT `correlativas_ibfk_1` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`) ON DELETE CASCADE,
  ADD CONSTRAINT `correlativas_ibfk_2` FOREIGN KEY (`id_materia_correlativa`) REFERENCES `materias` (`id_materia`) ON DELETE CASCADE;

--
-- Filtros para la tabla `inasistencias`
--
ALTER TABLE `inasistencias`
  ADD CONSTRAINT `inasistencias_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`) ON DELETE CASCADE,
  ADD CONSTRAINT `inasistencias_ibfk_2` FOREIGN KEY (`id_carrera`) REFERENCES `lista_carreras` (`id_carrera`),
  ADD CONSTRAINT `inasistencias_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `inscripciones_carreras`
--
ALTER TABLE `inscripciones_carreras`
  ADD CONSTRAINT `inscripciones_carreras_ibfk_1` FOREIGN KEY (`id_turno`) REFERENCES `turno_carrera` (`id_turno`);

--
-- Filtros para la tabla `inscripcion_f`
--
ALTER TABLE `inscripcion_f`
  ADD CONSTRAINT `inscripcion_f_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
  ADD CONSTRAINT `inscripcion_f_ibfk_3` FOREIGN KEY (`id_mesa`) REFERENCES `mesas_f` (`id_mesa`) ON DELETE CASCADE,
  ADD CONSTRAINT `inscripcion_f_ibfk_4` FOREIGN KEY (`id_mesa`) REFERENCES `mesas_f` (`id_mesa`) ON DELETE CASCADE;

--
-- Filtros para la tabla `intentos_materia`
--
ALTER TABLE `intentos_materia`
  ADD CONSTRAINT `intentos_materia_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
  ADD CONSTRAINT `intentos_materia_ibfk_2` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `licencias`
--
ALTER TABLE `licencias`
  ADD CONSTRAINT `licencias_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`) ON DELETE CASCADE,
  ADD CONSTRAINT `licencias_ibfk_2` FOREIGN KEY (`id_carrera`) REFERENCES `lista_carreras` (`id_carrera`),
  ADD CONSTRAINT `licencias_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `mesas_f`
--
ALTER TABLE `mesas_f`
  ADD CONSTRAINT `mesas_f_ibfk_1` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`),
  ADD CONSTRAINT `mesas_f_ibfk_2` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`),
  ADD CONSTRAINT `mesas_f_ibfk_3` FOREIGN KEY (`dni_suplente`) REFERENCES `profesores` (`dni_profesor`);

--
-- Filtros para la tabla `suplencias`
--
ALTER TABLE `suplencias`
  ADD CONSTRAINT `suplencias_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`),
  ADD CONSTRAINT `suplencias_ibfk_2` FOREIGN KEY (`id_carrera`) REFERENCES `lista_carreras` (`id_carrera`),
  ADD CONSTRAINT `suplencias_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);

--
-- Filtros para la tabla `titulos_profesores`
--
ALTER TABLE `titulos_profesores`
  ADD CONSTRAINT `titulos_profesores_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`) ON DELETE CASCADE;

--
-- Filtros para la tabla `toma_posesion`
--
ALTER TABLE `toma_posesion`
  ADD CONSTRAINT `toma_posesion_ibfk_1` FOREIGN KEY (`dni_profesor`) REFERENCES `profesores` (`dni_profesor`) ON DELETE CASCADE,
  ADD CONSTRAINT `toma_posesion_ibfk_2` FOREIGN KEY (`id_carrera`) REFERENCES `lista_carreras` (`id_carrera`),
  ADD CONSTRAINT `toma_posesion_ibfk_3` FOREIGN KEY (`id_materia`) REFERENCES `materias` (`id_materia`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
